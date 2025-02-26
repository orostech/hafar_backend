
from django.utils import timezone
from rest_framework import serializers
from .models import Like, Dislike, Match, UserSwipeAction, Visit
from users.models import Profile


def get_at(time):
    """Format the timestamp in a Tinder-like way"""
    now = timezone.now()
    diff = now - time
 
    
    if diff.days == 0:
        if diff.seconds < 3600:  # Less than an hour
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days}d ago"
    else:
        return time.strftime("%b %d")

class DislikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dislike
        fields = ['id', 'disliker', 'disliked', 'created_at']
        read_only_fields = ['disliker', 'created_at']


class ProfileMinimalSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='user.id')
    old_id = serializers.ReadOnlyField(source='user.old_id')
    age = serializers.SerializerMethodField()
    profile_photo = serializers.SerializerMethodField()
    is_new_user = serializers.SerializerMethodField()
    online_status= serializers.SerializerMethodField()
    is_premium = serializers.SerializerMethodField()
    latlng = serializers.SerializerMethodField()
    # distance = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id','old_id', 'display_name', 'age', 'profile_photo', 'bio','gender',
                  'is_new_user','online_status','is_premium'
                  ,'latlng'
                # ,'distance'
                  ]

    def get_age(self, obj):
        return obj.get_age()
    
    def get_is_new_user(self, obj):
        return obj.is_new_user
    
    def get_online_status(self,obj):
        return obj.online_status
    
    def get_is_premium(self, obj):
        return obj.user.active_subscription is not None

    def get_profile_photo(self, obj):
        photo = obj.user.photos.filter(is_primary=True).first()
        if photo:
            if not photo.image:
                return photo.image_url
            return photo.image.url
        return None
    
    # def get_distance(self, obj):
    #     # user = None
    #     # request = self.context.get('request')
    #     # print(request)
    #     # print('m e 1mo')
    #     # if request:
    #     #     user = request.user
    #     # else:
    #     #     user = self.context.get('user')
    #     # print('m edkc 1')
    #     # if obj.location and user.profile.location:
    #     #     print('m kx sde 1')
    #     #     return obj.location.distance(request.user.profile.location) * 100  # km
    #     return None
    
    def get_latlng(self, obj):
        return obj.latlng()

       

class VisitSerializer(serializers.ModelSerializer):
    profile = ProfileMinimalSerializer(source='visitor.profile', read_only=True)
    visited_at = serializers.SerializerMethodField()
    class Meta:
        model = Visit
        fields = ['visitor', 'visited', 'profile', 'created_at','visited_at']
        read_only_fields = ['visitor', 'created_at']

    def get_visited_at(self, obj):
         return get_at(obj.created_at)

class LikeSerializer(serializers.ModelSerializer):
    profile = ProfileMinimalSerializer(source='liker.profile', read_only=True)
    liked_at = serializers.SerializerMethodField()
    class Meta:
        model = Like
        fields = [ 'liker', 'liked','profile', 'like_type', 'created_at', 'is_active','liked_at']
        read_only_fields = ['liker', 'created_at']  

    def get_liked_at(self, obj):
        return get_at(obj.created_at)


class MatchSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    last_interaction_at = serializers.SerializerMethodField()
    class Meta:
        model = Match
        fields = ['user1', 'user2','profile', 'is_active',
                  'last_interaction_at', 'last_interaction',
                  ]
        read_only_fields = ['created_at', 'last_interaction']

    def get_profile(self, obj):
        if obj.user1 == self.context['request'].user:
            return ProfileMinimalSerializer(obj.user2.profile).data
        else:
            return ProfileMinimalSerializer(obj.user1.profile).data
        
    def get_last_interaction_at(self, obj):
         return get_at(obj.last_interaction)

class UserSwipeActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSwipeAction
        fields = ['id', 'user', 'target_user', 'action', 'created_at',
                 'target_age', 'target_distance', 'common_interests_count',
                 'lifestyle_similarity_score']
        read_only_fields = ['user', 'created_at']