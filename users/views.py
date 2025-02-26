# views.py
import requests
from rest_framework import viewsets, generics, filters,exceptions 
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, F
from django.utils import timezone
from match.serializers import ProfileMinimalSerializer
from notification.email_service import EmailService
from .models import OTP, Profile, User, UserPhoto, UserVideo, UserBlock, UserRating, generate_unique_username
from .serializers import (
    CurrentUserProfileSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, PasswordResetVerifySerializer, ProfileSerializer, UserPhotoSerializer, RegisterSerializer, UserVideoSerializer,
    UserBlockSerializer, UserRatingSerializer
)
from django.contrib.auth.hashers import make_password
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from .serializers import RegisterSerializer, LoginSerializer
from .models import Profile
from match.models import Visit
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class PasswordResetRequestView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)            
            # Create or update OTP
            OTP.objects.filter(user=user).delete()  # Invalidate previous OTPs
            otp = OTP.objects.create(user=user)
            
            # Send OTP via email
            EmailService().send_password_reset_otp(user, otp.code)
            
            return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetVerifyView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            
            user = User.objects.get(email=email)
            otp = OTP.objects.filter(user=user, code=code).first()
            if otp and otp.is_valid():
                return Response({"message": "OTP verified."}, status=status.HTTP_200_OK)
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(views.APIView):
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']
            
            user = User.objects.get(email=email)
            otp =  OTP.objects.filter(user=user, code=code).first()
            
            if otp and otp.is_valid():
                user.password = make_password(new_password)
                user.save()
                otp.is_used = True
                otp.save()
                return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GoogleLogin(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # Get the token from request data
            token = request.data.get('token')
            if not token:
                return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Verify token with Google
            response = requests.get(
                f'https://oauth2.googleapis.com/tokeninfo?id_token={token}')
            if response.status_code != 200:
                error_details = response.json()
                return Response({'error': error_details.get('error_description')}, status=status.HTTP_400_BAD)
            user_info = response.json()
            email = user_info.get('email')
            first_name = user_info.get('given_name')
            last_name = user_info.get('family_name')
            name = user_info.get('name')
            display_name = name or email.split('@')[0]
            username = generate_unique_username(email, display_name)

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create(
                    email=email,
                    first_name=first_name,
                    last_name= last_name,
                    email_verified=True,
                    username=username,
                    password=make_password(None)  # Set unusable password
                )

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            profile = user.profile
            profile_data = CurrentUserProfileSerializer(profile).data

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                **profile_data
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RegisterView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create verification token
            verification_token = get_random_string(64)
            user.verification_token = verification_token
            user.save()        
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            profile = user.profile
            profile_data = CurrentUserProfileSerializer(profile).data
           
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                **profile_data  # Unpack profile_data into the main dictionary
      
               
                # serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = authenticate(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
    
            if user:
                refresh = RefreshToken.for_user(user)
                profile = user.profile
                try:
                    context = {
                        'user': user,
                        'login_time': timezone.now().strftime("%Y-%m-%d %H:%M %Z"),
                        'device_info': request.META.get('HTTP_USER_AGENT', 'Unknown device'),
                        'location': self.get_location_from_ip(request),
                        'security_url': f"{settings.FRONTEND_URL}/security"
                    }
                    # EmailService().send_login_alert(user, context)
                except Exception as e:
                    print(f"Error sending login alert: {str(e)}")
                try:
                    profile_data = CurrentUserProfileSerializer(profile).data
                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        **profile_data 
                    })
                except:
                        return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_location_from_ip(self, request):
        ip = request.META.get('REMOTE_ADDR')
        # Implement IP geolocation lookup here if needed
        return ip or "Unknown location"

class VerifyEmailView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            user = User.objects.get(verification_token=token)
            if not user.email_verified:
                user.email_verified = True
                user.verification_token = None
                user.save()
                return Response({
                    'message': 'Email verified successfully'
                })
            return Response({
                'message': 'Email already verified'
            })
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid verification token'
            }, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationEmailView(views.APIView):
    def post(self, request):
        user = request.user
        if user.email_verified:
            return Response({
                'message': 'Email already verified'
            })
        
        # Create new verification token
        verification_token = get_random_string(64)
        user.verification_token = verification_token
        user.save()
        
        # Send verification email
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{verification_token}"
        context = {
            'user': user,
            'verification_url': verification_url
        }
        email_html = render_to_string('email/verify_email.html', context)
        email_text = render_to_string('email/verify_email.txt', context)
        
        send_mail(
            'Verify your email',
            email_text,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=email_html,
            fail_silently=False,
        )
        
        return Response({
            'message': 'Verification email sent'
        })

class UserRegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileMinimalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['display_name', 'bio']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_serializer_class(self):
        if self.action == 'me':
            return CurrentUserProfileSerializer
        if self.action == 'retrieve':
            return ProfileSerializer
        return super().get_serializer_class()

    def get_queryset(self):
       
        return Profile.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a profile and record the visit"""
        try:
            # Get the requested profile
            instance = self.get_object()

            if not instance.user:
                return Response({'error': 'Profile is missing an associated user.'}, status=status.HTTP_400_BAD_REQUEST)

            
            # # Only record visits for other users' profiles
            if request.user != instance.user:
                # Record the visit using get_or_create to prevent duplicates
                Visit.objects.get_or_create(
                    visitor=request.user,
                    visited=instance.user
                )
            # Proceed with normal retrieval
            serializer = self.get_serializer(instance,context={'request': request})
            return Response(serializer.data)
            
        except Exception as e:
            print(f"Profile retrieval error: {str(e)}",)
            return Response(
                {'error': 'Error retrieving profile'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['GET'])
    def me(self, request):
        profile = self.request.user.profile
        serializer = CurrentUserProfileSerializer(profile,context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['POST'])
    def updateme(self, request, *args, **kwargs):
        """
        Handle the update for the user's own profile.
        """
        profile = self.request.user.profile
        print( request.FILES.getlist('images'));
        serializer = CurrentUserProfileSerializer(
            profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
         # Handle image uploads
        if 'images' in request.FILES:
            for image in request.FILES.getlist('images'):
                UserPhoto.objects.create(user=request.user, image=image)

        self.perform_update(serializer)
         # Send WebSocket update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{request.user.id}',
            {
                'type': 'profile_update',
                'data': {
                    'message': 'Profile updated',
                    'data': serializer.data,
                    'updated_fields': list(request.data.keys())
                }
            }
        )
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def recommended_matches(self, request):
        """
        Returns recommended matches based on interests and preferences similarity
        """
        base_queryset = self.get_queryset()
        serializer = self.get_serializer(base_queryset, many=True)
        return Response(serializer.data)

class UserPhotoViewSet(viewsets.ModelViewSet):
    serializer_class = UserPhotoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPhoto.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserVideoViewSet(viewsets.ModelViewSet):
    serializer_class = UserVideoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserVideo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserBlockViewSet(viewsets.ModelViewSet):
    serializer_class = UserBlockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserBlock.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserRatingViewSet(viewsets.ModelViewSet):
    serializer_class = UserRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserRating.objects.filter(
            Q(rating_user__user=self.request.user) | 
            Q(rated_user__user=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(rating_user=self.request.user.profile)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_device_token(request):
    user = request.user
    device_token = request.data.get('device_token')
    if device_token:
        user.device_token = device_token
        user.save()
        return Response({'status': 'success'})
    return Response({'error': 'Invalid token'}, status=400)