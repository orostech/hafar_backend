# match/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from wallet.models import Transaction

class Like(models.Model):
    COIN_COST = {
        'REGULAR': 0,
        'SUPER': 10,
    }
    
    LIKE_TYPES = [
        ('REGULAR', 'Regular Like'),
        ('SUPER', 'Super Like'),
    ]

    liker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes_given')
    liked = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes_received')
    like_type = models.CharField(max_length=10, choices=LIKE_TYPES, default='REGULAR')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['liker', 'liked','is_active']),
        ]
        unique_together = ('liker', 'liked','is_active')

    @property
    def coin_cost(self):
        return self.COIN_COST[self.like_type]

class Dislike(models.Model):
    disliker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dislikes_given')
    disliked = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dislikes_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['disliker', 'disliked']),
        ]
        unique_together = ('disliker', 'disliked')

class Visit(models.Model):
    visitor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='visits', on_delete=models.CASCADE)
    visited = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='visited_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('visitor', 'visited') 
class Match(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_as_user1')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_interaction = models.DateTimeField(auto_now=True)
    is_premium = models.BooleanField(default=False)
    # premium_features = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ('user1', 'user2')
    
    def activate_premium_features(self, coins):
        """Activate premium match features"""
        if self.user1.wallet.deduct_coins(coins) and self.user2.wallet.deduct_coins(coins):
            self.is_premium = True
            self.premium_features = {
                'unlimited_messaging': True,
                'priority_support': True,
                'exclusive_content': True
            }
            self.save()
            return True
        return False

class SwipeLimit(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    daily_likes_count = models.PositiveIntegerField(default=0)
    daily_super_likes_count = models.PositiveIntegerField(default=0)
    daily_free_super_likes = models.PositiveIntegerField(default=1)
    ad_boost_remaining = models.PositiveIntegerField(default=0)
    last_reset = models.DateTimeField(default=timezone.now)
    
    def reset_if_needed(self):
        if timezone.now() - self.last_reset > timedelta(days=1):
            self.daily_likes_count = 0
            self.daily_super_likes_count = 0
            self.ad_boost_remaining = 0
            self.last_reset = timezone.now()
            self.save()
    
    def add_ad_boost(self, amount=5):
        self.ad_boost_remaining += amount
        self.save()

class UserPreferenceWeight(models.Model):
    """Stores weights for different matching criteria per user"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    distance_weight = models.FloatField(default=0.3)
    age_weight = models.FloatField(default=0.2)
    interests_weight = models.FloatField(default=0.3)
    lifestyle_weight = models.FloatField(default=0.2)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(distance_weight__gte=0) & 
                    models.Q(distance_weight__lte=1) &
                    models.Q(age_weight__gte=0) & 
                    models.Q(age_weight__lte=1) &
                    models.Q(interests_weight__gte=0) & 
                    models.Q(interests_weight__lte=1) &
                    models.Q(lifestyle_weight__gte=0) & 
                    models.Q(lifestyle_weight__lte=1)
                ),
                name='weights_between_0_and_1'
            )
        ]

class UserSwipeAction(models.Model):
    """Stores user swipe actions for machine learning"""
    ACTION_TYPES = [
        ('LIKE', 'Like'),
        ('DISLIKE', 'Dislike'),
        ('SUPERLIKE', 'Super Like')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='swipe_actions')
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_swipes')
    action = models.CharField(max_length=10, choices=ACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Store the profile attributes at the time of swipe for ML training
    target_age = models.IntegerField()
    target_distance = models.FloatField()
    common_interests_count = models.IntegerField()
    lifestyle_similarity_score = models.FloatField()

class BoostManager(models.Manager):
    def create_boost(self, user, duration, coin_cost):
        if user.wallet.deduct_coins(coin_cost):
            boost = self.create(
                user=user,
                duration=duration,
                is_active=True
            )
            Transaction.objects.create(
                user=user,
                amount=-coin_cost,
                transaction_type='SPEND',
                description=f'Profile boost for {duration} seconds'
            )
            return boost
        return None
class Boost(models.Model):
    DURATION_CHOICES = [
        (3600, '1 Hour'),
        (21600, '6 Hours'),
        (86400, '24 Hours'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    duration = models.PositiveIntegerField(choices=DURATION_CHOICES)
    start_time = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    objects = BoostManager()

    @classmethod
    def get_active_boosts(cls, user):
        return cls.objects.filter(
            user=user,
            is_active=True,
            end_time__gte=timezone.now()
        )

    @property
    def end_time(self):
        return self.start_time + timezone.timedelta(seconds=self.duration)