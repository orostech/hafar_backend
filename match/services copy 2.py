
# match/services.py
from django.db.models import Subquery, OuterRef
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
import numpy as np

from hafar_backend.match.models import UserSwipeAction
from hafar_backend.users.models import Profile

from .ml_matching_reale import MLMatchingService

class MatchingService:
    def __init__(self, user):
        self.user = user
        self.ml_service = MLMatchingService(user)
        self._prepare_data()

    def _prepare_data(self):
        """Precompute frequently accessed data"""
        self.user_location = Point(
            self.user.profile.longitude, 
            self.user.profile.latitude
        ) if self.user.profile.latitude else None

    def get_potential_matches(self, limit=100):
        """Hybrid recommendation system"""
        try:
            return self.ml_service.get_recommendations(limit)
        except Exception as e:
            logger.error(f"ML recommendations failed: {str(e)}")
            return self._get_fallback_matches(limit)

    def _get_fallback_matches(self, limit):
        """Rule-based fallback system"""
        return Profile.objects.annotate(
            distance=Distance('location', self.user_location)
        ).filter(
            age__range=(self.user.profile.min_age, self.user.profile.max_age),
            gender=self.user.profile.preferred_gender
        ).order_by('distance')[:limit]

    def update_recommendation_weights(self):
        """Reinforcement learning weight update"""
        successful_matches = Match.objects.filter(
            user1=self.user,
            messages__count__gt=10
        ).values_list('user2_id', flat=True)
        
        positive_actions = UserSwipeAction.objects.filter(
            user=self.user,
            target_user__in=successful_matches
        )
        
        # Update model with positive reinforcement
        if positive_actions.exists():
            self.ml_service.partial_fit(
                positive_actions.features(),
                np.ones(len(positive_actions))
            )

