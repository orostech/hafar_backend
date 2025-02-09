# views.py
from rest_framework import viewsets, generics, filters,exceptions 
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, F
from django.contrib.postgres.search import TrigramSimilarity
from datetime import date
from dateutil.relativedelta import relativedelta

from match.serializers import ProfileMinimalSerializer
from .models import Profile, User, UserPhoto, UserVideo, UserBlock, Interest, UserRating
from .serializers import (
    CurrentUserProfileSerializer, ProfileDetailSerializer, ProfileSerializer, UserPhotoSerializer, RegisterSerializer, UserVideoSerializer,
    UserBlockSerializer, InterestSerializer, UserRatingSerializer
)
# auth_views.py
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
                profile_data = CurrentUserProfileSerializer(profile).data
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    **profile_data  # Unpack profile_data into the main dictionary
                })
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    serializer_class = ProfileMinimalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['display_name', 'bio']

    def get_serializer_class(self):
        if self.action == 'me':
            return ProfileDetailSerializer
        if self.action == 'retrieve':
            return ProfileDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        try:
            user_profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            raise exceptions.NotFound('User profile does not exist')
        # Get blocked users
        blocked_users = UserBlock.objects.filter(
            Q(user=user) | Q(blocked_user=user)
        ).values_list('user', 'blocked_user')
        blocked_ids = set()
        for block in blocked_users: 
            blocked_ids.update(block)
  

        # Exclude blocked users, own profile, and inactive/suspended/banned/deactivated users
        base_queryset = Profile.objects.exclude(
            Q(user__id__in=blocked_ids) | 
            Q(user=user) | 
            Q(user_status__in=['IA', 'S', 'B', 'D'])  # Exclude inactive, suspended, banned, and deactivated users
        )
        
        # Apply filters based on user preferences
        queryset = base_queryset

        # Gender preference - only filter if interested_in is not 'Everyone'
        if user_profile.interested_in != 'E':
            queryset = queryset.filter(gender=user_profile.interested_in)

        # Apply age range filtering
        queryset = queryset.filter(
            date_of_birth__gte=date.today() - relativedelta(years=user_profile.maximum_age_preference),
            date_of_birth__lte=date.today() - relativedelta(years=user_profile.minimum_age_preference)
        )
        
        # Filter by profile visibility
        queryset = queryset.filter(profile_visibility='VE')  # Visible to Everyone

        # Order by verification status, putting verified users first
        queryset = queryset.order_by(
            F('is_verified').desc(),  # Place verified users first
            'created_at'  # Secondary ordering can be adjusted as needed
        )

        # # Location-based filtering if coordinates are available
        # if user_profile.latitude and user_profile.longitude:
        #     queryset = queryset.annotate(
        #         distance=((F('latitude') - user_profile.latitude) ** 2 + 
        #                  (F('longitude') - user_profile.longitude) ** 2) ** 0.5
        #     ).filter(
        #         distance__lte=user_profile.maximum_distance_preference / 111.0  # Rough km to degree conversion
        #     ).order_by('distance')

        return queryset
        # return Profile.objects.all()

    @action(detail=False, methods=['GET'])
    def me(self, request):
        profile = self.request.user.profile
        serializer = CurrentUserProfileSerializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['POST'])
    def updateme(self, request, *args, **kwargs):
        """
        Handle the update for the user's own profile.
        """
        profile = self.request.user.profile
        print( request.FILES.getlist('images'));
        # self.object = self.get_object()
        serializer = CurrentUserProfileSerializer(
            profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
         # Handle image uploads
        if 'images' in request.FILES:
            for image in request.FILES.getlist('images'):
                UserPhoto.objects.create(user=request.user, image=image)

        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def recommended_matches(self, request):
        """
        Returns recommended matches based on interests and preferences similarity
        """
        user_profile = Profile.objects.get(user=request.user)
        base_queryset = self.get_queryset()

        # Get user's interests
        user_interests = set(user_profile.interests.values_list('id', flat=True))

        # Annotate profiles with interest similarity score
        matches = []
        for profile in base_queryset:
            profile_interests = set(profile.interests.values_list('id', flat=True))
            interest_similarity = len(user_interests.intersection(profile_interests)) / \
                                len(user_interests.union(profile_interests)) if user_interests or profile_interests else 0

            # Calculate age similarity
            # user_age = (date.today() - user_profile.date_of_birth.date()).days / 365.25
            user_age = (date.today() - user_profile.date_of_birth).days / 365.25
            print(user_age)
            # profile_age = (date.today() - profile.date_of_birth.date()).days / 365.25
            profile_age = (date.today() - profile.date_of_birth).days / 365.25
            age_similarity = 1 - abs(user_age - profile_age) / 100  # Normalize age difference

            # Calculate overall match score
            match_score = (interest_similarity * 0.6) + (age_similarity * 0.4)

            matches.append({
                'profile': profile,
                'match_score': match_score
            })

        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Serialize and return top matches
        serializer = self.get_serializer([m['profile'] for m in matches[:10]], many=True)
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

class InterestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Interest.objects.all()
    serializer_class = InterestSerializer
    permission_classes = [IsAuthenticated]

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