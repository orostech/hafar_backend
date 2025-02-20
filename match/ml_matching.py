# match/ml_matching.py
from datetime import timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
# from django.db.models import Q, F, Count, Avg
from django.db.models import Count, Q
from .models import UserSwipeAction, Match
from users.models import Profile
from django.utils import timezone
from chat.models import Message

class MLMatchingService:
    def __init__(self, user):
        self.user = user
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.train_recommendation_model()

    def enhance_matches(self, base_matches, limit=100):
        """Enhance base matches with ML-based scoring"""
        # Ensure model is trained
        if not self.is_fitted:
            self.train_recommendation_model()

        enhanced_matches = []

        try:
            for profile in base_matches:
                # Calculate scores
                ml_score = self.get_compatibility_score(
                    self.user.profile, profile)
                success_rate = self.get_historical_success_rate(profile)

                # Combine scores with weights
                final_score = (ml_score * 0.6 + success_rate * 0.4)
                enhanced_matches.append((profile, final_score))

            # Sort by final score
            enhanced_matches.sort(key=lambda x: x[1], reverse=True)
            return [profile for profile, score in enhanced_matches[:limit]]

        except Exception as e:
            # Fallback to base matches if ML scoring fails
            print(f"ML scoring failed: {str(e)}")
            return base_matches[:limit]

    def train_recommendation_model(self):
        """Train recommendation model with fallback for insufficient data"""
        try:
            # Get successful matches based on active status and last interaction
            successful_matches = Match.objects.filter(
                is_active=True,
                last_interaction__isnull=False
            )

            training_pairs = []

            # Add positive examples from successful matches
            for match in successful_matches:
                user1_features = self.get_user_features(match.user1.profile)
                user2_features = self.get_user_features(match.user2.profile)
                if user1_features is not None and user2_features is not None:
                    training_pairs.append(user1_features.flatten())
                    training_pairs.append(user2_features.flatten())

            # Add negative examples from dislikes
            negative_actions = UserSwipeAction.objects.filter(action='DISLIKE')
            for action in negative_actions:
                user_features = self.get_user_features(action.user.profile)
                target_features = self.get_user_features(
                    action.target_user.profile)
                if user_features is not None and target_features is not None:
                    training_pairs.append(user_features.flatten())
                    training_pairs.append(target_features.flatten())

            # Create synthetic examples if needed
            if len(training_pairs) < 10:
                random_profiles = Profile.objects.order_by('?')[:20]
                for profile in random_profiles:
                    features = self.get_user_features(profile)
                    if features is not None:
                        training_pairs.append(features.flatten())

            # Fit scaler if we have data
            if training_pairs:
                X = np.vstack(training_pairs)
                self.scaler.fit(X)
                self.is_fitted = True
            # else:
            #     # Fallback initialization
            #     self.scaler.fit(np.zeros((1, 10)))
            #     self.is_fitted = True
            else:
                # Fallback: Initialize with zeros of the correct shape
                num_features = 10  # Adjust this based on the actual number of features
                self.scaler.fit(np.zeros((1, num_features)))
                self.is_fitted = True

        except Exception as e:
            print(f"Error training model: {str(e)}")
            self.scaler.fit(np.zeros((1, 10)))
            self.is_fitted = True

    def get_compatibility_score(self, profile1, profile2):
        """Calculate compatibility score between two profiles"""
        try:
            features1 = self.get_user_features(profile1)
            features2 = self.get_user_features(profile2)

            if features1 is None or features2 is None:
                return 0.5

            # Normalize features
            normalized_features1 = self.scaler.transform(features1)
            normalized_features2 = self.scaler.transform(features2)

            # Calculate similarity
            similarity = cosine_similarity(
                normalized_features1, normalized_features2)[0][0]

            # Scale to 0-1 range
            return (similarity + 1) / 2

        except Exception as e:
            print(f"Error calculating compatibility: {str(e)}")
            return 0.5

    def get_historical_success_rate(self, profile):
        """Calculate historical success rate for a profile"""
        try:
            total_matches = Match.objects.filter(
                Q(user1=profile.user) | Q(user2=profile.user),
                is_active=True
            ).count()

            successful_matches = Match.objects.filter(
                Q(user1=profile.user) | Q(user2=profile.user),
                is_active=True,
                last_interaction__isnull=False
            ).count()

            if total_matches == 0:
                return 0.5

            return successful_matches / total_matches

        except Exception as e:
            print(f"Error calculating success rate: {str(e)}")
            return 0.5

    def get_user_features(self, profile):
        """Extract numerical features from a user profile with error handling"""
        try:
            # Map 'do_you_have_kids' field
            # Add 'D' for "I don't like kids"
            kids_map = {'N': 0, 'S': 1, 'R': 2, 'D': 3}

            # Map 'smoking' field
            smoking_map = {'N': 0, 'S': 1, 'Y': 2}

            # Map 'drinking' field
            drinking_map = {'N': 0, 'S': 1, 'Y': 2}

            # Map 'relationship_goal' field
            relationship_goal_map = {'NSR': 0, 'CAS': 1, 'LTR': 2, 'MAR': 3}

            # response_rate = profile.user.received_messages.filter(
            # created_at__gte=timezone.now()-timedelta(days=7)
            #  ).count() / (profile.user.sent_messages.count() or 1)
            response_rate = Message.objects.filter(
                chat__user2=profile.user,
                created_at__gte=timezone.now()-timedelta(days=7)
            ).count() / (Message.objects.filter(sender=profile.user).count() or 1)

          
            features = np.array([
                float(profile.get_age() or 0),
                float(profile.latitude or 0),
                float(profile.longitude or 0),
                float(profile.height or 0),
                float(profile.weight or 0),
                # float(len(profile.interests.all())),
                # Use updated mapping
                float(kids_map.get(profile.do_you_have_kids, 0)),
                # Use updated mapping
                float(smoking_map.get(profile.smoking, 0)),
                # Use updated mapping
                float(drinking_map.get(profile.drinking, 0)),
                float(relationship_goal_map.get(profile.relationship_goal, 0)),

                float(response_rate),
                float(profile.last_seen.timestamp()),
                float(profile.completeness_score)
            ]).reshape(1, -1)
            return features
        except Exception as e:
            print(
                f"Error extracting features for profile {profile}: {str(e)}")
            return None
