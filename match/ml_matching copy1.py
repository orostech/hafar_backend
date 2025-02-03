# # match/ml_matching.py
# from sklearn.preprocessing import StandardScaler
# from sklearn.metrics.pairwise import cosine_similarity
# import numpy as np
# # from django.db.models import Q, F, Count, Avg
# from django.db.models import Count, Q
# from .models import UserSwipeAction, Match
# from users.models import Profile

# class MLMatchingService:
#     def __init__(self, user):
#         self.user = user
#         self.scaler = StandardScaler()
#         self.is_fitted = False   # Track whether the scaler has been fitted
        
#     def get_user_features(self, profile):
#         """Extract numerical features from a user profile"""
#         return np.array([
#             profile.get_age(),
#             profile.latitude if profile.latitude else 0,
#             profile.longitude if profile.longitude else 0,
#             profile.height if profile.height else 0,
#             profile.weight if profile.weight else 0,
#             len(profile.interests.all()),
#             profile.number_of_kids if profile.number_of_kids else 0,
#             # Encode categorical variables
#             {'N': 0, 'S': 1, 'R': 2}[profile.smoking],
#             {'N': 0, 'S': 1, 'R': 2}[profile.drinking],
#             {'NSR': 0, 'CAS': 1, 'LTR': 2, 'MAR': 3}[profile.relationship_goal],
#         ]).reshape(1, -1)
    
#     def train_recommendation_model(self):
#         """Train a recommendation model based on successful matches and user actions"""
#         # Get successful matches (those that led to conversations)
#         successful_matches = Match.objects.filter(
#             is_active=True
#         ).annotate(
#             message_count=Count('messages')
#         ).filter(
#             message_count__gt=5
#         )
        
#         # Get positive examples (successful matches)
#         positive_pairs = []
#         for match in successful_matches:
#             user1_features = self.get_user_features(match.user1.profile)
#             user2_features = self.get_user_features(match.user2.profile)
#             positive_pairs.extend([user1_features, user2_features])
            
#         # Get negative examples (dislikes)
#         negative_actions = UserSwipeAction.objects.filter(
#             action='DISLIKE'
#         )
#         negative_pairs = []
#         for action in negative_actions:
#             user_features = self.get_user_features(action.user.profile)
#             target_features = self.get_user_features(action.target_user.profile)
#             negative_pairs.extend([user_features, target_features])
            
#         # Combine and normalize features
#         X = np.vstack(positive_pairs + negative_pairs)
#         self.scaler.fit(X)
#         self.is_fitted = True  # Mark the scaler as fitted
        
#         return self.scaler
        
#     def get_compatibility_score(self, profile1, profile2):
#         """Calculate compatibility score between two profiles using ML"""

#         if not self.is_fitted:
#             raise RuntimeError("StandardScaler has not been fitted. Call 'train_recommendation_model' first.")
        
#         # Extract and normalize features
#         features1 = self.get_user_features(profile1)
#         features2 = self.get_user_features(profile2)
        
#         normalized_features1 = self.scaler.transform(features1)
#         normalized_features2 = self.scaler.transform(features2)
        
#         # Calculate similarity score
#         similarity = cosine_similarity(normalized_features1, normalized_features2)[0][0]
        
#         return similarity
        
#     def enhance_matches(self, base_matches, limit=20):
#         """Enhance base matches with ML-based scoring"""
#         # Get base matches from traditional algorithm
#         enhanced_matches = []
#         user_features = self.get_user_features(self.user.profile)
        
#         for profile in base_matches:
#             match_features = self.get_user_features(profile)
            
#             # Calculate multiple scores
#             ml_score = self.get_compatibility_score(self.user.profile, profile)
            
#             # Get historical success rate
#             success_rate = self.get_historical_success_rate(profile)
            
#             # Combine scores (you can adjust weights)
#             final_score = (ml_score * 0.6 + success_rate * 0.4)
            
#             enhanced_matches.append((profile, final_score))
            
#         # Sort by final score and return top matches
#         enhanced_matches.sort(key=lambda x: x[1], reverse=True)
#         return [profile for profile, score in enhanced_matches[:limit]]
        
#     def get_historical_success_rate(self, profile):
#         """Calculate historical success rate for a profile"""
#         total_matches = Match.objects.filter(
#             Q(user1=profile.user) | Q(user2=profile.user)
#         ).count()
        
#         successful_matches = Match.objects.filter(
#             Q(user1=profile.user) | Q(user2=profile.user),
#             is_active=True
#         ).annotate(
#             message_count=Count('messages')
#         ).filter(
#             message_count__gt=5
#         ).count()
        
#         if total_matches == 0:
#             return 0.5  # Default score for new profiles
            
#         return successful_matches / total_matches