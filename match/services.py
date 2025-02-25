# match/services.py
from django.db.models import Q, F, Count, Avg,Case,When,Value,IntegerField
from django.utils import timezone
from datetime import date, timedelta

from .ml_matching import MLMatchingService
from .models import Like, Dislike, Match, SwipeLimit, UserPreferenceWeight, UserSwipeAction
from users.models import Profile, UserBlock
import numpy as np
from dateutil.relativedelta import relativedelta
from sklearn.preprocessing import MinMaxScaler
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D



class MatchingService:
    def __init__(self, user,filter_params=None):
        self.user = user
        self.user_profile = user.profile
        self.preference_weights = UserPreferenceWeight.objects.get_or_create(user=user)[
            0]
        self.ml_service = MLMatchingService(user)
        self.filter_params = filter_params or {}

    def get_potential_matches(self, limit=100):
        """Get potential matches using both traditional and ML approaches"""
        # Get base matches using existing logic
        base_queryset = self._get_base_queryset()
    
        base_matches = self._score_profiles(base_queryset)
        # print(base_matches)
        # Get more for ML to filter
        base_profiles = [profile for profile, score in base_matches[:limit*2]]

        # # Enhance matches using ML
        enhanced_matches = self.ml_service.enhance_matches(
            base_profiles, limit=limit)

        return  enhanced_matches
        # return base_matches

    def _get_base_queryset(self):
        """Get base queryset of potential matches"""
        # Get users who haven't been liked/disliked yet
        excluded_users = set()

        excluded_users.update(Like.objects.filter(
            liker=self.user).values_list('liked', flat=True))
        excluded_users.update(Dislike.objects.filter(
            disliker=self.user).values_list('disliked', flat=True))
        excluded_users.update(UserBlock.objects.filter(Q(user=self.user) | Q(
            blocked_user=self.user)).values_list('user', 'blocked_user'))
       
        # Exclude blocked users, own profile, and inactive/suspended/banned/deactivated users
        base_queryset = Profile.objects.exclude(
            Q(user__in=excluded_users) |
            Q(user=self.user) |
            Q(user_status__in=['IA', 'S', 'B', 'D']) |
            Q(profile_visibility='PP')  # Filter by profile visibility
        )

        # Gender preference - only filter if interested_in is not 'Everyone'
        if self.user_profile.interested_in != 'E':
            base_queryset = base_queryset.filter(
                gender=self.user_profile.interested_in)
        print(len(base_queryset))
       # Age Filtering
        min_age = self.filter_params.get('min_age', self.user_profile.minimum_age_preference)
        max_age = self.filter_params.get('max_age', self.user_profile.maximum_age_preference)

        base_queryset = base_queryset.filter(
            date_of_birth__gte=date.today() - relativedelta(years=max_age),
            date_of_birth__lte=date.today() - relativedelta(years=min_age)
        )
   
        # Distance filtering
        max_distance = self.filter_params.get('max_distance', self.user_profile.maximum_distance_preference)
        print(self.user_profile.location)
        if self.user_profile.location:
            base_queryset = base_queryset.annotate(
                distance=Distance('location', self.user_profile.location)
            ).filter(
                distance__lte=D(km=max_distance)
            )

            # Ordering logic: Use Case to assign numeric values to `is_verified`
        base_queryset = base_queryset.annotate(
            verified_rank=Case(
                When(is_verified='VERIFIED', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )

        # Additional filters
        filter_conditions = Q()

        if self.filter_params.get('online_status'):  # Online users only
            filter_conditions &= Q(last_seen__gte=timezone.now() - timedelta(minutes=30))

        if self.filter_params.get('verified_only'):  # Only verified users
            filter_conditions &= Q(is_verified='VERIFIED')

        if self.filter_params.get('has_stories'):  # Users with stories
            filter_conditions &= Q(user__videos__video_type='STORY')
        
        # Apply combined filters
        if filter_conditions:
            base_queryset = base_queryset.filter(filter_conditions)
        print(len(base_queryset))
        # Ordering logic
        if self.user_profile.location:
            # return base_queryset.order_by('-verified_rank', '-distance')
            return base_queryset.order_by('-verified_rank', 'distance')

        return base_queryset.order_by('-verified_rank')
     


    def _score_profiles(self, queryset):
        """Score each profile based on multiple criteria"""
        scored_profiles = []

        for profile in queryset:
            # Calculate individual scores
            distance_score = self._calculate_distance_score(profile)
            age_score = self._calculate_age_score(profile)
            # interests_score = self._calculate_interests_score(profile)
            lifestyle_score = self._calculate_lifestyle_score(profile)

            # Calculate weighted average score
            total_score = (
                distance_score * self.preference_weights.distance_weight +
                age_score * self.preference_weights.age_weight +
                # interests_score * self.preference_weights.interests_weight +
                lifestyle_score * self.preference_weights.lifestyle_weight
            )

            scored_profiles.append((profile, total_score))

        return scored_profiles

    def _calculate_distance_score(self, profile):
        """Calculate distance-based score"""
        if not (self.user_profile.latitude and self.user_profile.longitude and
                profile.latitude and profile.longitude):
            return 0.5  # Default score if location not available

        distance = ((self.user_profile.latitude - profile.latitude) ** 2 +
                    (self.user_profile.longitude - profile.longitude) ** 2) ** 0.5
        # Convert to km (approximate)
        distance_km = distance * 111

        # Score decreases linearly with distance up to max_distance
        max_distance = self.user_profile.maximum_distance_preference
        return max(0, 1 - (distance_km / max_distance))

    def _calculate_age_score(self, profile):
        """Calculate age compatibility score"""
        target_age = profile.get_age()
        if not target_age:
            return 0.5

        min_age = self.user_profile.minimum_age_preference
        max_age = self.user_profile.maximum_age_preference

        if target_age < min_age or target_age > max_age:
            return 0

        # Higher score for ages in the middle of the preferred range
        mid_age = (min_age + max_age) / 2
        age_diff = abs(target_age - mid_age)
        age_range = (max_age - min_age) / 2

        return max(0, 1 - (age_diff / age_range))

    def _calculate_interests_score(self, profile):
        """Calculate interests compatibility score"""
        # user_interests = set(
        #     self.user_profile.interests.values_list('name', flat=True))
        # # profile_interests = 
        # # set(profile.interests.values_list('name', flat=True))

        # # if not user_interests or not profile_interests:
        # #     return 0.5

        # # Jaccard similarity
        # intersection = len(user_interests.intersection(profile_interests))
        # union = len(user_interests.union(profile_interests))

        # return intersection / union if union > 0 else 0
        return 0

    def _calculate_lifestyle_score(self, profile):
        """Calculate lifestyle compatibility score"""
        lifestyle_factors = [
            self.user_profile.smoking == profile.smoking,
            self.user_profile.drinking == profile.drinking,
            self.user_profile.relationship_goal == profile.relationship_goal,
            self.user_profile.dietary_preferences == profile.dietary_preferences
        ]

        return sum(1 for factor in lifestyle_factors if factor) / len(lifestyle_factors)

    def update_preference_weights(self):
        """Update preference weights based on successful matches"""
        recent_actions = UserSwipeAction.objects.filter(
            user=self.user,
            created_at__gte=timezone.now() - timedelta(days=30)
        )

        if recent_actions.exists():
            # Calculate average scores for liked profiles
            liked_profiles = recent_actions.filter(action__in=['LIKE', 'SUPERLIKE']).aggregate(
                avg_distance=Avg('target_distance'),
                avg_age=Avg('target_age'),
                # avg_interests=Avg('common_interests_count'),
                avg_lifestyle=Avg('lifestyle_similarity_score')
            )

            # Update weights based on the importance of each factor
            total = sum(liked_profiles.values())
            if total > 0:
                self.preference_weights.distance_weight = liked_profiles['avg_distance'] / total
                self.preference_weights.age_weight = liked_profiles['avg_age'] / total
                # self.preference_weights.interests_weight = liked_profiles['avg_interests'] / total
                self.preference_weights.lifestyle_weight = liked_profiles['avg_lifestyle'] / total
                self.preference_weights.save()
