# # Add to MatchingService
# from datetime import timedelta
# import numpy as np
# from sklearn.neighbors import BallTree
# from django.utils import timezone
# from django.db.models import Q, F, Count, Avg
# from .ml_matching_reale import EnhancedMLMatching
# from users.models import Profile, UserBlock
# import logging

# logger = logging.getLogger(__name__)
# class AdvancedMatchingService:
#     def __init__(self, user):
#         self.user = user
#         self.ml_engine = EnhancedMLMatching(user)
#         self._prepare_geo_index()
        
#     def _prepare_geo_index(self):
#         """Prepare geospatial index for location queries"""
#         self.location_tree = BallTree(
#             np.radians(Profile.objects.exclude(latitude__isnull=True)
#                        .values_list('latitude', 'longitude')),
#             metric='haversine'
#         )
        
#     def get_potential_matches(self, limit=100):
#         """Hybrid recommendation system"""
#         try:
#             # Get base candidates
#             base_query = self._base_query()
            
#             # Apply ML filtering
#             candidates = self.ml_engine.generate_recommendations(base_query)
            
#             # Apply real-time constraints
#             return self._apply_real_time_filters(candidates, limit)
            
#         except Exception as e:
#             logger.error(f"Matching failed: {str(e)}")
#             return self._fallback_matching(limit)

#     def _base_query(self):
#         """Base query with common filters"""
#         return Profile.objects.exclude(
#             Q(user=self.user) |
#             Q(user__in=UserBlock.objects.filter(blocker=self.user).values('blocked')) |
#             Q(user_status__in=['IA', 'S', 'B', 'D'])
#         ).annotate(
#             age=ExtractYear(Func(F('date_of_birth'), function='AGE')),
#             activity_score=Case(
#                 When(last_seen__gte=timezone.now()-timedelta(days=7), then=1),
#                 default=0.5
#             )
#         ).order_by('-activity_score', '-completeness_score')

#     def _apply_real_time_filters(self, candidates, limit):
#         """Apply real-time constraints"""
#         return sorted(
#             candidates,
#             key=lambda p: (
#                 -p.activity_score,
#                 -p.completeness_score,
#                 self._distance_to(p)
#             )
#         )[:limit]

#     def _distance_to(self, profile):
#         """Get cached distance calculation"""
#         if not hasattr(profile, '_cached_distance'):
#             profile._cached_distance = self._calculate_distance(profile)
#         return profile._cached_distance