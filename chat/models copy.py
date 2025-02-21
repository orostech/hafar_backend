from collections import defaultdict
from django.db import models
from django.conf import settings
from django.utils import timezone
# from datetime import timedelta
from match.models import Match
from django.contrib.postgres.search import SearchVectorField

from wallet.models import Transaction
# from cryptography.hazmat.primitives import serialization

class Chat(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats_initiated')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats_received')
    match = models.ForeignKey(Match, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Permission flags
    requires_acceptance = models.BooleanField(default=True)
    is_accepted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user1', 'user2')
        ordering = ['-last_activity']

    def __str__(self):
        return f"Chat between {self.user1} and {self.user2}"

    def get_other_user(self, user):
        return self.user2 if user == self.user1 else self.user1

    def update_last_activity(self):
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
class MessageManager(models.Manager):
    def create_message(self, sender, chat, content_type, content):
        # Check if chat is active and accepted
        if not chat.is_active or (chat.requires_acceptance and not chat.is_accepted):
            raise ValueError("Cannot send message to this chat")
        
        message = self.model(
            sender=sender,
            chat=chat,
            content_type=content_type,
            content=content
        )
        message.save()
        
        # Update chat's last activity
        chat.update_last_activity()
        return message
class Message(models.Model):
    CONTENT_TYPES = [
        ('TEXT', 'Text'),
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('AUDIO', 'Audio'),
        ('GIF', 'GIF'),
        ('STICKER', 'Sticker'),
    ]
    
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    search_vector = SearchVectorField(null=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, default='TEXT')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    deleted_for = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='deleted_messages')
    expires_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    reactions = models.JSONField(default=dict)
    # encrypted_content = models.BinaryField()
    # sender_public_key = models.BinaryField()
    # receiver_public_key = models.BinaryField()
    
    objects = MessageManager()

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender} in {self.chat}"

    def mark_as_read(self, user):
        if user == self.chat.get_other_user(self.sender) and not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])

    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at
    
    # def update_reactions(self):
    #     self.reactions = defaultdict(int)
    #     for reaction in self.message_reactions.all():
    #     # self.messagereaction_set.all():
    #         self.reactions[reaction.emoji] += 1
    #     self.save()
    def update_reactions(self):
        """Updates the reactions field in the Message model"""
        reactions = defaultdict(int)
        for reaction in self.message_reactions.all():
            reactions[reaction.emoji] += 1
        self.reactions = dict(reactions)  # Convert defaultdict to regular dict before saving
        self.save(update_fields=['reactions'])
    
    @property
    def pin_count(self):
        return self.pinnedmessage_set.count()

    # @property
    # def contentt(self):
    #     return E2EEncryptor.decrypt_message(
    #         self.receiver.private_key,
    #         self.sender_public_key,
    #         self.encrypted_content
    #     )
class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='message_reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=5)  # Store as Unicode emoji or shortcode
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')
class PinnedMessage(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='pinned_messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pinned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')
class ChatSettings(models.Model):
    THEME_CHOICES = [
        ('DEFAULT', 'Default'),
        ('DARK', 'Dark'),
        ('LIGHT', 'Light'),
        ('CUSTOM', 'Custom'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='DEFAULT')
    custom_theme = models.CharField(max_length=20, blank=True)
    notification_enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'chat')
class MessageRequest(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True)
    coins_paid = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']

    def accept(self):
        self.status = 'ACCEPTED'
        self.save()
        # Create or activate chat
        chat, created = Chat.objects.get_or_create(
            user1=self.sender,
            user2=self.receiver,
            defaults={'requires_acceptance': False, 'is_accepted': True}
        )
        if not created:
            chat.is_active = True
            chat.is_accepted = True
            chat.save()
        # If there's an initial message in the request, create a new message
        if self.message.strip():
            Message.objects.create(
                sender=self.sender,
                chat=chat,
                content_type='TEXT',  # Assuming text type for the initial request message
                content=self.message,
                created_at=timezone.now()
            )
        if self.is_paid:
            Transaction.objects.create(
                user=self.sender,
                amount=self.coins_paid,
                transaction_type='SPEND',
                description=f"Paid message to {self.receiver.username}"
            )

        return chat
        

    def reject(self):
        self.status = 'REJECTED'
        self.save()

    # def create_chat_message(self):
    #     if self.status == 'ACCEPTED' and self.chat.is_accepted:
    #         Message.objects.create(
    #             sender=self.sender,
    #             chat=self.chat,
    #             content=self.message,
    #             content_type='TEXT'
    #         )
    #         if self.is_paid:
    #             Transaction.objects.create(
    #                 user=self.sender,
    #                 amount=self.coins_paid,
    #                 transaction_type='SPEND',
    #                 description=f"Paid message to {self.receiver.username}"
    #             )

# class DeviceKey(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     public_key = models.BinaryField()
#     private_key = models.BinaryField(encrypted=True)  # Use django-encrypted-fields
#     is_primary = models.BooleanField(default=False)
    
#     def generate_keys(self):
#         private_key = x25519.X25519PrivateKey.generate()
#         self.public_key = private_key.public_key().public_bytes(
#             encoding=serialization.Encoding.Raw,
#             format=serialization.PublicFormat.Raw
#         )
#         self.private_key = private_key.private_bytes(
#             encoding=serialization.Encoding.Raw,
#             format=serialization.PrivateFormat.Raw,
#             encryption_algorithm=serialization.NoEncryption()
#         )