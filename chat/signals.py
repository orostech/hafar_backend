from collections import defaultdict
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Count
from .models import MessageReaction

@receiver(post_save, sender=MessageReaction)
@receiver(post_delete, sender=MessageReaction)
def update_message_reactions(sender, instance, **kwargs):
    print('me')
    """Update the message's reactions field when a reaction is added or removed"""
    message = instance.message
    reactions = defaultdict(int)
    print(message)
    print(reactions)

    for reaction in message.message_reactions.all():
        reactions[reaction.emoji] += 1
        print(reactions[reaction.emoji])

    message.reactions = dict(reactions)  # Store as JSON
    message.save(update_fields=['reactions'])