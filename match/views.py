# match/views.py
from math import radians, sin, cos, sqrt, atan2
from datetime import timedelta
import logging
from users.models import Profile, UserBlock
from django.db import transaction
from rest_framework import viewsets, status, pagination, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.core.cache import cache
from django.utils import timezone
from .services import MatchingService
# from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

# from users.models import Profile
from .models import Like, Dislike, Match, SwipeLimit, UserSwipeAction, Visit
# from .services_real import MatchingService
from .serializers import (
    LikeSerializer, DislikeSerializer, MatchSerializer, ProfileMinimalSerializer, VisitSerializer
)
from django.conf import settings
from django.contrib.gis.db.models.functions import Distance as DistanceFunc

logger = logging.getLogger(__name__)

DAILY_LIKE_LIMIT = 10
DAILY_SUPER_LIKE_LIMIT = 15 if settings.DEBUG else 3


def get_swipe_limits(user):
    cache_key = f'swipe_limits_{user.id}'
    limits = cache.get(cache_key)
    if not limits:
        limits = SwipeLimit.objects.get_or_create(user=user)[0]
        cache.set(cache_key, limits, timeout=60*5)  # Cache for 5 minutes
    return limits


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers using Haversine formula."""
    if None in [lat1, lon1, lat2, lon2]:
        return 0.0

    # Convert degrees to radians
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Earth radius in kilometers (approximate)
    radius = 6371.0
    return radius * c


class MatchActionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def get_serializer_class(self):
        if self.action in ['like', 'super_like']:
            return LikeSerializer
        elif self.action == 'dislike':
            return DislikeSerializer
        return MatchSerializer

    @action(detail=False, methods=['POST'])
    def like(self, request):
        try:
            liked_user_id = request.data.get('liked')
            like_type = request.data.get('like_type', 'REGULAR').upper()
            user = request.user
            # Input validation
            if not liked_user_id:
                return Response({'error': 'Liked user ID is required'},
                                status=status.HTTP_400_BAD_REQUEST)
            if user.id == liked_user_id:
                return Response({'error': 'Cannot like yourself'},
                                status=status.HTTP_400_BAD_REQUEST)

            if like_type not in [choice[0] for choice in Like.LIKE_TYPES]:
                return Response({'error': 'Invalid like type'},
                                status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():

                swipe_limit, created = SwipeLimit.objects.select_for_update().get_or_create(user=user)
                swipe_limit.reset_if_needed()

                # Check limits
                if like_type == 'SUPER' and swipe_limit.daily_super_likes_count >= DAILY_SUPER_LIKE_LIMIT:
                    return Response(
                        {'error': 'Daily super like limit reached'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                elif swipe_limit.daily_likes_count >= DAILY_LIKE_LIMIT:
                    if swipe_limit.add_ad_boost > 0:
                        swipe_limit.add_ad_boost -= 1
                        swipe_limit.save()
                    else:
                        return Response(
                            {'error': 'Daily like limit reached'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS
                        )

                 # Remove any existing dislikes
                Dislike.objects.filter(
                    disliker=user,
                    disliked_id=liked_user_id
                ).delete()

                Like.objects.update_or_create(
                    liker=user,
                    liked_id=liked_user_id,
                    defaults={
                        'is_active': True,
                        'like_type': like_type}
                )
                mutual_like = Like.objects.filter(
                    liker_id=liked_user_id,
                    liked=user,
                    is_active=True
                ).exists()
                if mutual_like:
                    Match.objects.update_or_create(
                        user1=user,
                        user2_id=liked_user_id,
                        defaults={
                            'is_active': True,
                            'last_interaction': timezone.now()
                        }
                    )
                # Update counters
                if like_type == 'SUPER':
                    swipe_limit.daily_super_likes_count += 1
                else:
                    swipe_limit.daily_likes_count += 1
                swipe_limit.save()

                return Response({
                    'match_created': mutual_like,
                    'remaining_likes': (DAILY_LIKE_LIMIT - swipe_limit.daily_likes_count) + swipe_limit.ad_boost_remaining,
                    'remaining_super_likes': DAILY_SUPER_LIKE_LIMIT - swipe_limit.daily_super_likes_count
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Like error for user {user.id}: {str(e)}")
            return Response({'error': 'Internal server error'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['DELETE'])
    def unlike(self, request):
        try:
            liked_user_id = request.data.get('liked')
            user = request.user

            # Validate input
            if not liked_user_id:
                return Response({'error': 'Liked user ID is required'},
                                status=status.HTTP_400_BAD_REQUEST)
            if user.id == liked_user_id:
                return Response({'error': 'Cannot unlike yourself'},
                                status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Deactivate the like
                likes_to_deactivate = Like.objects.filter(
                    liker=user,
                    liked_id=liked_user_id,
                    is_active=True
                )
                if likes_to_deactivate.exists():
                    likes_to_deactivate.update(is_active=False)

                match_to_deactivate = Match.objects.filter(
                    Q(user1=user, user2_id=liked_user_id) |
                    Q(user1_id=liked_user_id, user2=user),
                    is_active=True
                )
                if match_to_deactivate.exists():
                    match_to_deactivate.update(
                        is_active=False, last_interaction=timezone.now())

            return Response({'status': 'success'})
        except Exception as e:
            logger.error(f"Unlike error: {str(e)}")
            return Response({'error': 'Failed to unlike'}, status=400)

    @action(detail=False, methods=['POST'])
    def dislike(self, request):
        try:
            disliked_user_id = request.data.get('disliked')
            user = request.user

            # Validate input
            if not disliked_user_id:
                return Response({'error': 'disliked user ID is required'},
                                status=status.HTTP_400_BAD_REQUEST)
            if user.id == disliked_user_id:
                return Response({'error': 'Cannot dislike yourself'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Check if dislike already exists using select_for_update to prevent race conditions
            with transaction.atomic():
                dislike, created = Dislike.objects.get_or_create(
                    disliker=request.user,
                    disliked_id=disliked_user_id
                )
                if not created:
                    return Response({'status': 'already disliked', 'code': 'already_disliked'},
                                    status=status.HTTP_200_OK)
                # Deactivate existing likes (instead of delete) using bulk_update
                likes_to_deactivate = Like.objects.filter(
                    Q(liker=user, liked_id=disliked_user_id) |
                    Q(liker_id=disliked_user_id, liked=user),
                    is_active=True
                )
                if likes_to_deactivate.exists():
                    likes_to_deactivate.update(is_active=False)

                # Deactivate matches and update last interaction
                matches_to_deactivate = Match.objects.filter(
                    Q(user1=user, user2_id=disliked_user_id) |
                    Q(user1_id=disliked_user_id, user2=user),
                    is_active=True
                )
                if matches_to_deactivate.exists():
                    matches_to_deactivate.update(
                        is_active=False,
                        last_interaction=timezone.now()
                    )

                # Update swipe limits
                swipe_limit, _ = SwipeLimit.objects.get_or_create(user=user)
                swipe_limit.reset_if_needed()

                # Return remaining swipes count for UI updates

            return Response({
                'status': 'success',
                'remaining_likes': (DAILY_LIKE_LIMIT - swipe_limit.daily_likes_count) + swipe_limit.ad_boost_remaining,
                'remaining_super_likes': DAILY_SUPER_LIKE_LIMIT - swipe_limit.daily_super_likes_count
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Dislike error for user {user.id}: {str(e)}")
            return Response({'error': 'Failed to process dislike'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['DELETE'])
    def undislike(self, request):
        try:
            disliked_user_id = request.data.get('disliked')
            user = request.user

            # Validate input
            if not disliked_user_id:
                return Response({'error': 'Disliked user ID is required'},
                                status=status.HTTP_400_BAD_REQUEST)
            if user.id == disliked_user_id:
                return Response({'error': 'Cannot undislike yourself'},
                                status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Delete the dislike
                dislike = Dislike.objects.filter(
                    disliker=user,
                    disliked_id=disliked_user_id
                )
                if dislike.exists():
                    dislike.delete()
                else:
                    return Response({'error': 'No active dislike found'},
                                    status=status.HTTP_404_NOT_FOUND)

            return Response({'status': 'success'})
        except Exception as e:
            logger.error(f"Undislike error for user {user.id}: {str(e)}")
            return Response({'error': 'Failed to undislike'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def matches(self, request):
        """Get all active matches for the current user"""
        matches = Match.objects.filter(
            Q(user1=request.user) | Q(user2=request.user),
            is_active=True
        ).order_by('-last_interaction')

        serializer = self.get_serializer(matches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def potential_matches(self, request):
        """Get filtered potential matches"""
        profile = request.user.profile
        selected_states = request.query_params.getlist('selected_states', [])
        selected_states_ids = [int(s) for s in selected_states if s.isdigit()]
        filters = {
            'min_age': int(request.query_params.get('min_age', profile.minimum_age_preference)),
            'max_age': int(request.query_params.get('max_age', profile.maximum_age_preference)),
            'max_distance': float(request.query_params.get('max_distance', profile.maximum_distance_preference)),
            'gender': request.query_params.get('gender', profile.interested_in),
            'relationship_goal': request.query_params.get('relationship_goal'),
            'verified_only': request.query_params.get('verified') == 'true',
            'online_status': request.query_params.get('online') == 'true',
            'has_stories': request.query_params.get('stories') == 'true',
            'selected_states': selected_states_ids,
        }
        # Update user preferences with filters
        updated = False
        if filters['min_age'] != profile.minimum_age_preference:
            profile.minimum_age_preference = filters['min_age']
            updated = True
        if filters['max_age'] != profile.maximum_age_preference:
            profile.maximum_age_preference = filters['max_age']
            updated = True
        if filters['max_distance'] != profile.maximum_distance_preference:
            profile.maximum_distance_preference = filters['max_distance']
            updated = True
        if filters['gender'] != profile.interested_in:
            profile.interested_in = filters['gender']
            updated = True
        if updated:
            profile.save()

        matching_service = MatchingService(request.user, filter_params=filters)
        potential_matches = matching_service.get_potential_matches(limit=100)
        paginator = pagination.PageNumberPagination()
        result_page = paginator.paginate_queryset(potential_matches, request,)
        serializer = ProfileMinimalSerializer(result_page, many=True,
                                              context={'request': request}
                                              )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['POST'])
    def unmatch(self, request, pk=None):
        """Unmatch from a user"""
        match = Match.objects.filter(
            Q(user1=request.user, user2_id=pk) |
            Q(user1_id=pk, user2=request.user),
            is_active=True
        ).first()

        if not match:
            return Response(
                {'error': 'Match not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        match.is_active = False
        match.save()

        # Remove associated likes
        Like.objects.filter(
            Q(liker=request.user, liked_id=pk) |
            Q(liker_id=pk, liked=request.user)
        ).update(is_active=False)

        return Response({'status': 'success'})

    @action(detail=False, methods=['GET'])
    def remaining_swipes(self, request):
        """Get remaining swipes for the current user"""
        swipe_limit, created = SwipeLimit.objects.get_or_create(user=request.user)[
            0]
        swipe_limit.reset_if_needed()

        return Response({
            'remaining_likes': (DAILY_LIKE_LIMIT - swipe_limit.daily_likes_count) + swipe_limit.ad_boost_remaining,
            'remaining_super_likes': DAILY_SUPER_LIKE_LIMIT - swipe_limit.daily_super_likes_count
        })

    @action(detail=False, methods=['POST'])
    def ad_swipe_boost(self, request):
        """Add ad swipe boost to the user"""
        user = request.user
        swipe_limit, created = SwipeLimit.objects.get_or_create(user=user)
        swipe_limit.add_ad_boost()
        swipe_limit.reset_if_needed()

        return Response({
            'remaining_likes': (DAILY_LIKE_LIMIT - swipe_limit.daily_likes_count) + swipe_limit.ad_boost_remaining,
            'remaining_super_likes': DAILY_SUPER_LIKE_LIMIT - swipe_limit.daily_super_likes_count
        })


class InteractionsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'likes':
            return LikeSerializer
        elif self.action == 'matches':
            return MatchSerializer
        elif self.action == 'visits':
            return VisitSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """
        Return queryset based on the action being performed.
        Default to an empty queryset since this ViewSet is action-specific.
        """
        user = self.request.user

        if self.action == 'likes':
            return Like.objects.filter(
                liked=user,
                is_active=True
            ).order_by('-created_at')

        elif self.action == 'matches':
            return Match.objects.filter(
                Q(user1=user) | Q(user2=user),
                is_active=True
            ).order_by('-last_interaction')

        elif self.action == 'visits':
            return Visit.objects.filter(
                visited=user
            ).order_by('-created_at')
        # Default to empty queryset for other actions
        return Like.objects.none()

    @action(detail=False, methods=['GET'])
    def dashboard(self, request):
        """Get all interaction counts for dashboard"""
        user = request.user
        one_week_ago = timezone.now() - timedelta(days=7)

        # Get counts with efficient queries
        likes_received = Like.objects.filter(
            liked=user,
            is_active=True,
            created_at__gte=one_week_ago
        ).count()

        matches = Match.objects.filter(
            Q(user1=user) | Q(user2=user),
            is_active=True
        ).count()

        visitors = Visit.objects.filter(
            visited=user,
            created_at__gte=one_week_ago
        ).values('visitor').distinct().count()

        return Response({
            'new_likes': likes_received,
            'active_matches': matches,
            'recent_visitors': visitors,
            # 'is_premium': user.profile.is_premium if hasattr(user, 'profile') else False
        })

    @action(detail=False, methods=['GET'])
    def likes(self, request):
        """Get likes received by the user"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['GET'])
    def matches(self, request):
        """Get active matches"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['GET'])
    def visits(self, request):
        """Get profile visits"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


# class NearByPagination(pagination.PageNumberPagination):
#     page_size = 50  # Set the number of items per page
#     # Allow client to override, e.g. ?page_size=20
#     page_size_query_param = 'page_size'
#     max_page_size = 100


class NearbyUsersView(views.APIView):
    permission_classes = [IsAuthenticated]
    # pagination_class = NearByPagination

    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        max_distance = request.query_params.get('distance', 500)  # km

        if not request.user.profile.location:
            return Response({'error': 'Missing coordinates'}, status=400)

        try:
            user = request.user
            user_point = user.profile.location
            excluded_users = set()

            excluded_users.update(Like.objects.filter(
                liker=user).values_list('liked', flat=True))
            excluded_users.update(Dislike.objects.filter(
                disliker=user).values_list('disliked', flat=True))
            excluded_users.update(UserBlock.objects.filter(Q(user=user) | Q(
                blocked_user=user)).values_list('user', 'blocked_user'))
            # Point(float(lng), float(lat), srid=4326)
            base_query  = Profile.objects.filter(
                location__distance_lte=(user_point, Distance(km=max_distance)),
            ).exclude(Q(user__in=excluded_users) |
                      Q(user=user) | Q(user_status__in=['IA', 'S', 'B', 'D']) | Q(profile_visibility='PP'))
       
            # base_query = base_queryset
            # Apply Gender Filtering
            if user.profile.interested_in != 'E':
                base_query = base_query.filter(
                    gender=user.profile.interested_in)
                
            # Sort by Distance
            profiles = base_query.annotate(distance=DistanceFunc('location', user_point)).order_by('distance')[:50]

           

            # If we have fewer than 50, relax gender constraints
            if len(profiles) < 50 and user.profile.interested_in != 'E':
                additional_profiles = Profile.objects.filter(
                    location__distance_lte=(user_point, Distance(km=max_distance))
                ).exclude(Q(user__in=excluded_users) | Q(user_status__in=['IA', 'S', 'B', 'D']) | Q(profile_visibility='PP')).annotate(
                    distance=DistanceFunc('location', user_point)
                ).order_by('distance')[:50 - len(profiles)]

                profiles = list(profiles) + list(additional_profiles)

            

            serializer = ProfileMinimalSerializer(profiles, many=True,
                                                  context={'request': request}
                                                  )
            return Response({'data':serializer.data})
        except Exception as e:
            logger.error(f"Nearby users error: {str(e)}")
            return Response({'error': 'Failed to fetch nearby users'}, status=500)
