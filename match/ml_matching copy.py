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
#         self.is_fitted = False
#         # Train the model immediately upon initialization
#         self.train_recommendation_model()

#     def enhance_matches(self, base_matches, limit=100):
#         """Enhance base matches with ML-based scoring"""
#         # Ensure model is trained
#         if not self.is_fitted:
#             self.train_recommendation_model()
            
#         enhanced_matches = []
        
#         try:
#             for profile in base_matches:
#                 # Calculate multiple scores
#                 ml_score = self.get_compatibility_score(self.user.profile, profile)
#                 success_rate = self.get_historical_success_rate(profile)
                
#                 # Combine scores
#                 final_score = (ml_score * 0.6 + success_rate * 0.4)
#                 enhanced_matches.append((profile, final_score))
                
#             # Sort by final score and return top matches
#             enhanced_matches.sort(key=lambda x: x[1], reverse=True)
#             return [profile for profile, score in enhanced_matches[:limit]]
            
#         except Exception as e:
#             # Fallback to base matches if ML scoring fails
#             print(f"ML scoring failed: {str(e)}")
#             return base_matches[:limit]

#     def train_recommendation_model(self):
#         """Train recommendation model with fallback for insufficient data"""
#         try:
#             # Get successful matches
#             successful_matches = Match.objects.filter(
#                 is_active=True
#             ).annotate(
#                 message_count=Count('messages')
#             ).filter(
#                 message_count__gt=5
#             )
            
#             # Collect training data
#             training_pairs = []
            
#             # Add positive examples from successful matches
#             for match in successful_matches:
#                 user1_features = self.get_user_features(match.user1.profile)
#                 user2_features = self.get_user_features(match.user2.profile)
#                 training_pairs.extend([user1_features, user2_features])
            
#             # Add negative examples from dislikes
#             negative_actions = UserSwipeAction.objects.filter(action='DISLIKE')
#             for action in negative_actions:
#                 user_features = self.get_user_features(action.user.profile)
#                 target_features = self.get_user_features(action.target_user.profile)
#                 training_pairs.extend([user_features, target_features])
            
#             # If we don't have enough data, create synthetic examples
#             if len(training_pairs) < 10:  # Minimum threshold for training
#                 random_profiles = Profile.objects.order_by('?')[:20]
#                 for profile in random_profiles:
#                     training_pairs.append(self.get_user_features(profile))
            
#             # Combine and normalize features
#             if training_pairs:
#                 X = np.vstack(training_pairs)
#                 self.scaler.fit(X)
#                 self.is_fitted = True
#             else:
#                 # Initialize with identity transformation if no data
#                 self.scaler.fit([[0] * 10])  # Match feature vector length
#                 self.is_fitted = True
                
#         except Exception as e:
#             print(f"Error training model: {str(e)}")
#             # Initialize with identity transformation as fallback
#             self.scaler.fit([[0] * 10])
#             self.is_fitted = True

#     # def get_compatibility_score(self, profile1, profile2):
#     #     """Calculate compatibility score between two profiles"""
#     #     try:
#     #         features1 = self.get_user_features(profile1)
#     #         features2 = self.get_user_features(profile2)
            
#     #         # Normalize features
#     #         normalized_features1 = self.scaler.transform([features1])
#     #         normalized_features2 = self.scaler.transform([features2])
            
#     #         # Calculate cosine similarity
#     #         similarity = cosine_similarity(normalized_features1, normalized_features2)[0][0]
            
#     #         # Scale to 0-1 range
#     #         return (similarity + 1) / 2
            
#     #     except Exception as e:
#     #         print(f"Error calculating compatibility: {str(e)}")
#     #         return 0.5
#     def get_compatibility_score(self, profile1, profile2):
#         """Calculate compatibility score between two profiles"""
#         try:
#             features1 = self.get_user_features(profile1)
#             features2 = self.get_user_features(profile2)
            
#             # Normalize features
#             normalized_features1 = self.scaler.transform([features1])
#             normalized_features2 = self.scaler.transform([features2])
            
#             # Calculate cosine similarity
#             similarity = cosine_similarity(normalized_features1, normalized_features2)[0][0]
            
#             # Scale to 0-1 range
#             # return (similarity + 1) / 2
#             return similarity
            
#         except Exception as e:
#             print(f"Error calculating compatibility: {str(e)}")
#             return 0.5
      
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
    
#     # def get_historical_success_rate(self, profile):
#     #     """Calculate historical success rate for a profile"""
#     #     try:
#     #         total_matches = Match.objects.filter(
#     #             Q(user1=profile.user) | Q(user2=profile.user),
#     #             is_active=True
#     #         ).count()
            
#     #         successful_matches = Match.objects.filter(
#     #             Q(user1=profile.user) | Q(user2=profile.user),
#     #             is_active=True,
#     #             last_interaction__isnull=False
#     #         ).count()
            
#     #         if total_matches == 0:
#     #             return 0.5
            
#     #         return successful_matches / total_matches
            
#     #     except Exception as e:
#     #         print(f"Error calculating success rate: {str(e)}")
#     #         return 0.5
    
#     # NEW RUBBISH
#     # def get_user_features(self, profile):
#     #     """Extract numerical features from a user profile"""
#     #     try:
#     #         features = [
#     #             profile.get_age() or 0,
#     #             float(profile.latitude or 0),
#     #             float(profile.longitude or 0),
#     #             profile.interests.count(),
#     #             int(profile.is_verified),
#     #             len(profile.bio or ''),
#     #             {'N': 0, 'S': 1, 'R': 2}.get(profile.smoking, 0),
#     #             {'N': 0, 'S': 1, 'R': 2}.get(profile.drinking, 0),
#     #             {'CA': 0, 'FR': 1, 'LT': 2, 'SR': 3}.get(profile.relationship_goal, 0),
#     #             {'OM': 0, 'VG': 1, 'VE': 2, 'PE': 3}.get(profile.dietary_preferences, 0)
#     #         ]
#     #         return features
#     #     except Exception as e:
#     #         print(f"Error extracting features: {str(e)}")
#     #         return [0] * 10

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
    
#     # Rest of the methods remain the same...