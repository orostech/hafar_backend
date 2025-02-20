from datetime import date, timedelta
import string
from django.utils import timezone
import random
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager,PermissionsMixin
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.contrib.auth.hashers import make_password
from django.core.validators import FileExtensionValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.contrib.gis.db import models as gis_models
from gift.models import VirtualGift
from subscription.models import UserSubscription
from wallet.payment_handlers import FlutterwaveHandler
from django.contrib.postgres.indexes import GistIndex

from .countries_states import COUNTRY_CHOICES, NIGERIA_STATES
from .const import ( ACCOUNT_STATUS_CHOICES, BODY_TYPE_CHOICES, COMPLEXION_CHOICES, DIETARY_PREFERENCES_CHOICES, DO_YOU_HAVE_KIDS_CHOICES, DO_YOU_HAVE_PETS_CHOICES, DRINKING_CHOICES, GENDER_CHOICES, INTEREST_CATEGORIES, INTEREST_IN_CHOICES, RELATIONSHIP_CHOICES, RELATIONSHIP_STATUS_CHOICES, SMOKING_CHOICES, USER_TYPE_CHOICES, VERIFICATION_STATUS_CHOICES, VISIBILITY_CHOICES)

def generate_unique_username(email, display_name=''):
    """
    Generate a unique username based on email and display name.
    Handles special characters and ensures uniqueness by adding random numbers if needed.
    """
    # First try to use display name if provided
    if display_name:
        base_username = slugify(display_name)  # Handles special characters better than replace
    else:
        # Fall back to email prefix
        base_username = slugify(email.split('@')[0])

    # Remove any remaining invalid characters
    base_username = ''.join(c for c in base_username if c.isalnum() or c == '-')
    
    # Ensure base username isn't too long (leaving room for numbers)
    base_username = base_username[:30]
    
    # Try the base username first
    username = base_username
    counter = 1
    
    # Keep trying new usernames until we find a unique one
    while User.objects.filter(username=username).exists():
        # Generate a random number between 1000 and 9999
        random_num = random.randint(1000, 9999)
        username = f"{base_username}-{random_num}"
        counter += 1
        # Prevent infinite loops
        if counter > 100:
            raise ValueError("Unable to generate unique username after 100 attempts")
    
    return username

class CustomUserManager(BaseUserManager):
    use_in_migrations = True
    def _create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        display_name = extra_fields.get('display_name', '')
        # username = generate_unique_username(email, display_name=display_name,)
        # Generate unique username
        username = generate_unique_username(email, display_name=display_name)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self , email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)


    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    old_id =  models.CharField( unique=True, max_length=255, blank=True, null=True)
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True
    )
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    device_token = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
  

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    class Meta:
        verbose_name = ('user')
        verbose_name_plural = ('users')

    def __str__(self):
        return f"{self.username}"

    def get_profile_photo(self):
        photo = self.photos.filter(is_primary=True).first()
        if photo:
            if not photo.image:
                return photo.image_url
            return photo.image.url
        return None

    @property
    def available_coins(self):
        return self.wallet.balance
    
    def purchase_coins(self, package):
        """Handle coin purchases"""
        handler = FlutterwaveHandler()
        return handler.initialize_payment(self, package['amount'], package['coins'])
    
    def send_gift(self, receiver, gift_type):
        """Send virtual gift to another user"""
        gift_costs = {
            'ROSE': 50,
            'CHOCOLATE': 100,
            'DIAMOND': 500
        }
        cost = gift_costs.get(gift_type)
        
        if cost and self.wallet.deduct_coins(cost):
            VirtualGift.objects.create(
                sender=self,
                receiver=receiver,
                gift_type=gift_type,
                coins_value=cost
            )
            return True
        return False
    
    # def activate_premium(self, tier):
    #     """Activate premium subscription"""
    #     tiers = {
    #         'BASIC': 500,
    #         'VIP': 1000,
    #         'PREMIUM': 2000
    #     }
    #     cost = tiers.get(tier)
        
    #     if cost and self.wallet.deduct_coins(cost):
    #         PremiumSubscription.objects.update_or_create(
    #             user=self,
    #             defaults={
    #                 'tier': tier,
    #                 'end_date': timezone.now() + timezone.timedelta(days=30),
    #                 'coin_cost': cost,
    #                 'is_active': True
    #             }
    #         )
    #         return True
    #     return False

    @property
    def active_subscription(self):
        return self.subscriptions.filter(
            is_active=True,
            end_date__gt=timezone.now()
        ).first()

    def activate_subscription(self, plan):
        """Purchase subscription using coins"""
        print(plan.coin_price)
        print(self.wallet.balance)
        if self.wallet.balance >= plan.coin_price:
            if self.wallet.deduct_coins(plan.coin_price):
                UserSubscription.objects.create(
                    user=self,
                    plan=plan,
                    is_active=True
                )
                return True
        return False

class Profile(models.Model):
    # Basic Information
    user = models.OneToOneField(settings.AUTH_USER_MODEL,primary_key=True, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=20, default='Unknown')
    bio = models.TextField(blank=True)
    date_of_birth  = models.DateField(null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES,help_text="What gender do you want to match with?")
    
    # Profession
    profession = models.CharField(max_length=15, null=True, blank=True)

    # Location Fields
    # location = gis_models.PointField(null=True, blank=True)  # Requires PostGIS
    location = gis_models.PointField(null=True, blank=True, geography=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=100, blank=True,null=True,)
    country = models.CharField(max_length=100, blank=True)
 

    # Current Location Field
    selected_address = models.CharField(max_length=255, blank=True, null=True)
    selected_state = models.CharField(max_length=100, choices=NIGERIA_STATES, null=True)
    selected_country = models.CharField(max_length=100, blank=True, choices=COUNTRY_CHOICES,  default= 'NG')
    selected_lga = models.CharField(max_length=100, blank=True,null=True)

    # Account Details
    user_type = models.CharField(max_length=1, choices=USER_TYPE_CHOICES, default='S')
    is_verified = models.CharField(max_length=50, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')

    # Privacy Settings
    user_status = models.CharField(max_length=2, choices=ACCOUNT_STATUS_CHOICES, default='IA' )
    profile_visibility = models.CharField(max_length=2, choices=VISIBILITY_CHOICES, default='VE' )
    show_online_status = models.BooleanField(default=True)
    show_distance = models.BooleanField(default=True)
    show_last_seen = models.BooleanField(default=True)

    # Preferences
    # interests = models.ManyToManyField('Interest', blank=True) 
    relationship_goal = models.CharField( max_length=3, choices=RELATIONSHIP_CHOICES, default='NSR')
    interested_in = models.CharField(max_length=6, choices=INTEREST_IN_CHOICES,default='E')
    minimum_age_preference = models.IntegerField(
        default=18,
        validators=[MinValueValidator(18), MaxValueValidator(100)]
    )
    maximum_age_preference = models.IntegerField(
        default=100,
        validators=[MinValueValidator(18), MaxValueValidator(100)]
    )
    maximum_distance_preference = models.IntegerField(
        default=100,
        help_text="Maximum distance in kilometers"
    )
    
    # Lifestyle
    body_type = models.CharField(max_length=2, choices=BODY_TYPE_CHOICES, default='AV')
    complexion = models.CharField(max_length=2, choices=COMPLEXION_CHOICES, default='MD')
    do_you_have_kids = models.CharField(choices=DO_YOU_HAVE_KIDS_CHOICES, default='D')
    do_you_have_pets = models.CharField(max_length=1, choices=DO_YOU_HAVE_PETS_CHOICES, default='D')
    weight = models.PositiveIntegerField(null=True, blank=True, help_text="Weight in kilograms (kg)")
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Height in centimeters (cm)")
    dietary_preferences = models.CharField(max_length=2, choices=DIETARY_PREFERENCES_CHOICES, blank=True)

    # Health Habits
    smoking = models.CharField(max_length=1, choices=SMOKING_CHOICES, default='N')
    drinking = models.CharField(max_length=1, choices=DRINKING_CHOICES, default='N')
    
    # Social Information
    relationship_status = models.CharField( max_length=3, choices=RELATIONSHIP_STATUS_CHOICES, default='NSR')
  
    # Social Links
    instagram_handle = models.CharField(max_length=100, blank=True, null=True)
    facebook_link = models.URLField(blank=True, null=True)
   
    # Activity
    last_seen = models.DateTimeField(auto_now=True)    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Notification Preference
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    new_matches_notitication = models.BooleanField(default=True)
    new_messages_notitication = models.BooleanField(default=True)
    app_updates = models.BooleanField(default=True)
    profile_view_notitication = models.BooleanField(default=True)
    likes_received_notitication = models.BooleanField(default=True)
    message_price = models.PositiveIntegerField(
        default=0,
        help_text="Coins required to message this user directly"
    )
    allow_vip_direct_messages = models.BooleanField(
        default=True,
        help_text="Allow VIP users to message directly"
    )
    require_initial_request = models.BooleanField(
        default=True,
        help_text="Require message requests for first contact"
    )
    welcome_email_sent = models.BooleanField(default=False)

    class Meta:
        indexes = [
            GistIndex(fields=['location']),
            models.Index(fields=['gender', 'relationship_goal']),
            models.Index(fields=['last_seen']),
            models.Index(fields=['created_at']),
        ]

    # Ratings & Reviews
    def average_rating(self):
        ratings = self.ratings_received.all()
        if ratings.exists():
            return sum(rating.value for rating in ratings) / ratings.count()
        return 0
    
    def get_age(self):
        if self.date_of_birth:
            return (date.today() - self.date_of_birth).days // 365
        return None
    
    @property
    def has_profile_video(self):
        return self.user.videos.filter(video_type='PROFILE').exists()
    
    @property
    def latest_story(self):
        return self.user.videos.filter(video_type='STORY').first()
    
    @property
    def location_coordinates(self):
        """ Returns a tuple of (latitude, longitude) for easy use. """
        return (self.latitude, self.longitude)

    def is_near(self, other_profile, max_distance_km):
        if self.location and other_profile.location:
            distance = self.location.distance(other_profile.location) / 1000  # Convert from meters to kilometers
            return distance <= max_distance_km
        return False

    @property
    def online_status(self):
        """ Returns the online status of the user. """
        if (timezone.now() - self.last_seen) < timedelta(minutes=5):
            return  'ONLINE'
        elif (timezone.now() - self.last_seen) < timedelta(minutes=30):
            return 'AWAY'
        else:
            return 'OFFLINE'

    @property
    def is_new_user(self):
        """
        Determines if the user is considered new (within 7 days of joining)
        """
        return (timezone.now() - self.created_at) <= timedelta(days=15)

    def get_user_recency(self):
        """
        Returns a more detailed description of user's newness
        """
        days_since_join = (timezone.now() - self.joined_at).days
        if days_since_join <= 1:
            return 'Brand New'
        elif days_since_join <= 7:
            return 'New User'
        return 'Existing User'
    
    def update_last_seen(self):
        """
        Manually update last_seen timestamp.
        Useful for specific actions like sending messages or updating profile.
        """
        self.__class__.objects.filter(id=self.id).update(
            last_seen=timezone.now()
        )
    
    @property
    def last_active_time(self):
        """
        Returns a human-readable last active time
        """
        if not self.last_seen:
            return "Never"
            
        now = timezone.now()
        diff = now - self.last_seen
        
        if diff < timezone.timedelta(minutes=5):
            return "Online"
        elif diff < timezone.timedelta(hours=1):
            minutes = diff.seconds // 60
            return f"Active {minutes} minutes ago"
        elif diff < timezone.timedelta(days=1):
            hours = diff.seconds // 3600
            return f"Active {hours} hours ago"
        else:
            days = diff.days
            return f"Active {days} days ago"
        
    @property
    def completeness_score(self):
        """Calculate profile completeness score"""
        required_fields = [
            self.bio,
            self.date_of_birth,
            self.latitude,
            self.longitude,
            # self.interests.exists(),
            self.user.photos.exists() 
        ]
        completed = sum(1 for field in required_fields if field)
        return completed / len(required_fields)
    
 
    # @property
    # def age(self):
    #     return (timezone.now().date() - self.birthdate).days // 365
    
    # @property
    # def location(self):
    #     return self.profile.location
    
    # def common_interests_with(self, other_user):
    #     return self.interests.filter(id__in=other_user.interests.all())


class UserRating(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    rated_user = models.ForeignKey(Profile, related_name='ratings_received', on_delete=models.CASCADE) 
    rating_user = models.ForeignKey(Profile, related_name='ratings_given', on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('rated_user', 'rating_user')

    def __str__(self):
        return f"{self.rating_user.username} rated {self.rated_user.user.username}: {self.value} stars"
    
# class Interest(models.Model):
#     name = models.CharField(max_length=50, unique=True, primary_key=True)
#     def __str__(self):
#         return self.name
    
class UserBlock(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocks_made')
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocks_received')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'blocked_user')

class UserPhoto(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(
        upload_to='user_photos/%Y/%m/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    image_url = models.URLField(blank=True,null=True) 
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_primary=True),
                name='unique_primary_photo'
            )
        ]

    def save(self, *args, **kwargs):
        # If this is being set as primary, unset any existing primary photo
        if self.is_primary:
            UserPhoto.objects.filter(
                user=self.user, 
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        # If this is the first photo, make it primary
        if not self.pk and not UserPhoto.objects.filter(user=self.user).exists():
            self.is_primary = True
            self.order = 0
        
        # If no order is set, put it at the end
        if self.order == 0:
            last_order = UserPhoto.objects.filter(
                user=self.user
            ).aggregate(models.Max('order'))['order__max']
            self.order = (last_order or 0) + 1

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # If this was the primary photo and there are other photos,
        # make the next photo primary
        if self.is_primary:
            next_photo = UserPhoto.objects.filter(
                user=self.user
            ).exclude(id=self.id).order_by('order').first()
            if next_photo:
                next_photo.is_primary = True
                next_photo.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Photo {self.order} for {self.user.username}"
    
def validate_file_size(value):
    # 10MB for audio, adjust as needed
    max_size = 10 * 1024 * 1024  
    if value.size > max_size:
        raise ValidationError(f'File size must be no more than {max_size/1024/1024}MB')

def validate_video_size(value):
    # 100MB for video, adjust as needed
    max_size = 100 * 1024 * 1024
    if value.size > max_size:
        raise ValidationError(f'Video size must be no more than {max_size/1024/1024}MB')

class UserAudioRecording(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='audio_recordings'
    )
    audio_file = models.FileField(
        upload_to='user_audio/%Y/%m/',
        validators=[
            FileExtensionValidator(['mp3', 'wav', 'm4a']),
            validate_file_size
        ]
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(  # Duration in seconds
        validators=[MaxValueValidator(300)]  # Max 5 minutes
    )
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username}'s audio: {self.title}"

class UserVideo(models.Model):
    VIDEO_TYPES = [
        ('PROFILE', 'Profile Video'),
        ('STORY', 'Story Video'),
        ('POST', 'Post Video'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    video_file = models.FileField(
        upload_to='user_videos/%Y/%m/',
        validators=[
            FileExtensionValidator(['mp4', 'mov', 'avi']),
            validate_video_size
        ]
    )
    thumbnail = models.ImageField(
        upload_to='video_thumbnails/%Y/%m/',
        blank=True,
        null=True
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(  # Duration in seconds
        validators=[MaxValueValidator(600)]  # Max 10 minutes
    )
    video_type = models.CharField(
        max_length=10,
        choices=VIDEO_TYPES,
        default='POST'
    )
    is_public = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username}'s video: {self.title}"

# Update Profile model to include video preferences
class VideoPreference(models.Model):
    profile = models.OneToOneField('Profile', on_delete=models.CASCADE, related_name='video_preferences')
    autoplay_videos = models.BooleanField(default=True)
    video_quality = models.CharField(
        max_length=10,
        choices=[
            ('AUTO', 'Auto'),
            ('LOW', 'Low'),
            ('MEDIUM', 'Medium'),
            ('HIGH', 'High')
        ],
        default='AUTO'
    )
    save_to_device = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.profile.user.username}'s video preferences"

def generate_otp():
    # str(random.randint(100000, 999999))
    code = ''.join(random.choices(string.digits, k=6))
    print("Generated OTP:", code)
    return code

class OTP(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otp')
    code  = models.CharField(max_length=6,default=generate_otp)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    def __str__(self):
        return f"{self.user.username}'s OTP"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    

