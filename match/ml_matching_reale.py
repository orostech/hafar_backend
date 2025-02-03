# # match/ml_matching.py
# import logging
# import numpy as np
# import pandas as pd
# from sklearn.pipeline import Pipeline
# from sklearn.compose import ColumnTransformer
# from sklearn.preprocessing import StandardScaler, OneHotEncoder
# from sklearn.ensemble import GradientBoostingClassifier
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import roc_auc_score
# from django.db.models import Count, Q, F, Subquery
# from django.db import transaction
# from django_redis import get_redis_connection
# from django.contrib.gis.db.models.functions import Distance
# from .models import UserSwipeAction, Match
# from users.models import Profile
# from django.utils import timezone

# logger = logging.getLogger(__name__)

# class EnhancedMLMatching:
#     def __init__(self, user):
#         self.user = user
#         self.redis = get_redis_connection("default")
#         self.model = None
#         self.feature_pipeline = None
#         self._initialize_components()
        
#     def _initialize_components(self):
#         """Initialize ML models and feature processors"""
#         self._load_or_train_model()
#         self._create_feature_pipeline()
        
#     def _create_feature_pipeline(self):
#         """Create feature processing pipeline"""
#         self.feature_pipeline = ColumnTransformer([
#             ('numerical', StandardScaler(), [
#                 'age_diff',
#                 'distance_km',
#                 'interest_overlap',
#                 'profile_completeness'
#             ]),
#             ('categorical', OneHotEncoder(handle_unknown='ignore'), [
#                 'relationship_goal_match',
#                 'lifestyle_compatibility'
#             ])
#         ])
    
#     def _load_or_train_model(self):
#         """Load cached model or train new one"""
#         cache_key = f"ml_model_{self.user.id}"
#         cached_model = self.redis.get(cache_key)
        
#         if cached_model:
#             self.model = pickle.loads(cached_model)
#         else:
#             self._train_model()
            
#     def _train_model(self):
#         """Train gradient boosted model with enhanced features"""
#         try:
#             with transaction.atomic():
#                 # Get expanded training data
#                 train_data = self._prepare_training_data()
                
#                 if len(train_data) < 1000:
#                     self._use_global_model()
#                     return

#                 X = self.feature_pipeline.fit_transform(train_data)
#                 y = train_data['match_success']
                
#                 X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
                
#                 self.model = GradientBoostingClassifier(
#                     n_estimators=200,
#                     learning_rate=0.05,
#                     max_depth=5
#                 )
#                 self.model.fit(X_train, y_train)
                
#                 # Validate model performance
#                 auc = roc_auc_score(y_test, self.model.predict_proba(X_test)[:, 1])
#                 if auc < 0.7:
#                     raise ValueError("Model performance insufficient")
                
#                 self._cache_model()

#         except Exception as e:
#             logger.error(f"Model training failed: {str(e)}")
#             self._use_global_model()

#     def _prepare_training_data(self):
#         """Prepare training data with enhanced features"""
#         positive_samples = self._get_positive_samples()
#         negative_samples = self._get_negative_samples()
#         return pd.concat([positive_samples, negative_samples]).sample(frac=1)

#     def _get_positive_samples(self):
#         """Get successful matches with enhanced features"""
#         return Match.objects.filter(
#             Q(user1=self.user) | Q(user2=self.user),
#             is_active=True,
#             messages__count__gt=5
#         ).annotate(
#             age_diff=Abs(F('user1__profile__age') - F('user2__profile__age')),
#             distance_km=Distance('user1__profile__location', 'user2__profile__location') / 1000,
#             interest_overlap=Count(
#                 Case(
#                     When(user1__profile__interests__in=Subquery(
#                         Profile.objects.filter(user=OuterRef('user2')).values('interests')
#                     ), then=1),
#                     output_field=IntegerField()
#                 )
#             ),
#             relationship_goal_match=Case(
#                 When(user1__profile__relationship_goal=F('user2__profile__relationship_goal'), then=1),
#                 default=0
#             ),
#             profile_completeness=(
#                 F('user1__profile__completeness_score') + 
#                 F('user2__profile__completeness_score')
#             ) / 2,
#             lifestyle_compatibility=Concat(
#                 F('user1__profile__smoking'),
#                 F('user2__profile__smoking'),
#                 output_field=CharField()
#             ),
#             match_success=1
#         ).values()

#     def _get_negative_samples(self):
#         """Get negative interactions with enhanced features"""
#         return UserSwipeAction.objects.filter(
#             user=self.user,
#             action='DISLIKE'
#         ).annotate(
#             age_diff=Abs(F('user__profile__age') - F('target_user__profile__age')),
#             distance_km=Distance('user__profile__location', 'target_user__profile__location') / 1000,
#             interest_overlap=Count(
#                 Case(
#                     When(user__profile__interests__in=Subquery(
#                         Profile.objects.filter(user=OuterRef('target_user')).values('interests')
#                     ), then=1),
#                     output_field=IntegerField()
#                 )
#             ),
#             relationship_goal_match=Case(
#                 When(user__profile__relationship_goal=F('target_user__profile__relationship_goal'), then=1),
#                 default=0
#             ),
#             profile_completeness=(
#                 F('user__profile__completeness_score') + 
#                 F('target_user__profile__completeness_score')
#             ) / 2,
#             lifestyle_compatibility=Concat(
#                 F('user__profile__smoking'),
#                 F('target_user__profile__smoking'),
#                 output_field=CharField()
#             ),
#             match_success=0
#         ).values()

#     def generate_recommendations(self, candidates):
#         """Generate recommendations with diversity"""
#         try:
#             # Feature engineering
#             features = self._engineer_features(candidates)
            
#             # Predict probabilities
#             scores = self.model.predict_proba(features)[:, 1]
            
#             # Combine with freshness score
#             freshness_scores = np.array([self._freshness_score(p) for p in candidates])
#             combined_scores = scores * 0.8 + freshness_scores * 0.2
            
#             # Apply diversity sampling
#             return self._diverse_sampling(candidates, combined_scores)
            
#         except Exception as e:
#             logger.error(f"Recommendation failed: {str(e)}")
#             return self._fallback_recommendations(candidates)

#     def _engineer_features(self, candidates):
#         """Create advanced feature set"""
#         features = []
#         for profile in candidates:
#             features.append({
#                 'age_diff': abs(self.user.profile.age - profile.age),
#                 'distance_km': self._calculate_distance(profile),
#                 'interest_overlap': self._interest_overlap(profile),
#                 'profile_completeness': profile.completeness_score,
#                 'relationship_goal_match': int(
#                     self.user.profile.relationship_goal == profile.relationship_goal
#                 ),
#                 'lifestyle_compatibility': (
#                     self.user.profile.smoking + profile.smoking
#                 )
#             })
#         return self.feature_pipeline.transform(pd.DataFrame(features))

#     def _calculate_distance(self, profile):
#         """Calculate precise distance using Haversine formula"""
#         if None in [self.user.profile.latitude, self.user.profile.longitude,
#                     profile.latitude, profile.longitude]:
#             return 0
            
#         lat1, lon1 = np.radians(self.user.profile.latitude), np.radians(self.user.profile.longitude)
#         lat2, lon2 = np.radians(profile.latitude), np.radians(profile.longitude)
        
#         dlat = lat2 - lat1
#         dlon = lon2 - lon1
        
#         a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
#         return 6371 * 2 * np.arcsin(np.sqrt(a))  # Earth radius in km

#     def _interest_overlap(self, profile):
#         """Calculate Jaccard similarity of interests"""
#         user_interests = set(self.user.profile.interests.values_list('id', flat=True))
#         target_interests = set(profile.interests.values_list('id', flat=True))
#         intersection = len(user_interests & target_interests)
#         union = len(user_interests | target_interests)
#         return intersection / union if union > 0 else 0

#     def _freshness_score(self, profile):
#         """Score based on profile freshness"""
#         days_since_update = (timezone.now() - profile.updated_at).days
#         return max(0, 1 - days_since_update / 30)

#     def _diverse_sampling(self, candidates, scores, n_clusters=10):
#         """Ensure diverse recommendations using clustering"""
#         from sklearn.cluster import KMeans
        
#         # Get embeddings for clustering
#         embeddings = np.array([
#             [p.age, p.latitude or 0, p.longitude or 0, 
#              len(p.interests.all()), p.completeness_score]
#             for p in candidates
#         ])
        
#         # Cluster candidates
#         clusters = KMeans(n_clusters=n_clusters).fit_predict(embeddings)
        
#         # Select top from each cluster
#         selected = []
#         for cluster_id in range(n_clusters):
#             cluster_mask = clusters == cluster_id
#             cluster_scores = scores[cluster_mask]
#             top_idx = np.argpartition(cluster_scores, -3)[-3:]  # Top 3 per cluster
#             selected.extend(np.where(cluster_mask)[0][top_idx])
            
#         return [candidates[i] for i in np.unique(selected)]