# # notifications/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from match.models import Like, Visit, Match
# from .models import Notification
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# from django.db import transaction
# import logging


# logger = logging.getLogger(__name__)

# @receiver(post_save, sender=Visit)
# def create_visit_notification(sender, instance, created, **kwargs):
#     """Create a notification when someone visits a user's profile."""
#     if created:
#         try:
#             pass
#             # # Use atomic transaction and on_commit for data consistency
#             # def _create_notification():
#             #     try:
#             #         Notification.objects.create(
#             #             recipient=instance.visited,
#             #             actor=instance.visitor,
#             #             verb='VISIT',
#             #             target_id=instance.id
#             #         )
#             #         logger.debug(f"Created visit notification for {instance.visited.id}")
#             #     except Exception as inner_e:
#             #         logger.error(
#             #             f"Failed to create visit notification: {str(inner_e)}\n"
#             #             f"Visit ID: {instance.id}\n"
#             #             f"Visitor: {instance.visitor.id}\n"
#             #             f"Visited: {instance.visited.id}",
#             #             exc_info=True
#             #         )

#             # transaction.on_commit(_create_notification)
            
#         except Exception as e:
#             logger.error(
#                 f"Visit notification creation failed: {str(e)}\n"
#                 f"Visit ID: {instance.id}",
#                 exc_info=True
#             )

# @receiver(post_save, sender=Like)
# def create_like_notification(sender, instance, created, **kwargs):
#     if created:
#         pass
#         # try:
#         #     verb = 'LIKE' if instance.like_type == 'REGULAR' else 'SUPER_LIKE'
#         #     def create_notification():
#         #          Notification.objects.create(
#         #             recipient=instance.liked,
#         #             actor=instance.liker,
#         #             verb=verb,
#         #             target_id=instance.id
#         #         )
#         #     transaction.on_commit(create_notification)
#         # except Exception as e:
#         #    print(f"Error creating notification: {str(e)}")
#         #    print(
#         #     f"Notification error for Like {instance.id}: "
#         #     f"Recipient: {instance.liked_id}, "
#         #     f"Actor: {instance.liker_id}, "
#         #     f"Verb: {verb}, "
#         #     f"Error: {str(e)}",
#         #     exc_info=True
#         # )

# # @receiver(post_save, sender=Like)
# # def create_like_notification(sender, instance, created, **kwargs):
# #     if created:
# #         try:
          
# #                         # Determine the verb based on the like type
# #             verb = 'LIKE' if instance.like_type == 'REGULAR' else 'SUPER_LIKE'
# #             print(instance.id)
# #             print(f"Recipient: {instance.liked} (type: {type(instance.liked)})")
# #             print(f"Actor: {instance.liker} (type: {type(instance.liker)})")
# #             print(f"Verb: {verb} (type: {type(verb)})")

# #             # Create the notification
# #             Notification.objects.create(
# #                 recipient=instance.liked,
# #                 actor=instance.liker,
# #                 verb=verb,
# #                 target_id=instance.id  # ID of the Like instance
# #             )
# #         except Exception as e:
# #             # Log the error for debugging purposes
# #             print(f"Error creating notification for like: {str(e)}")

# @receiver(post_save, sender=Visit)
# def create_visit_notification(sender, instance, created, **kwargs):
#     if created:
#         Notification.objects.create(
#             recipient=instance.visited,
#             actor=instance.visitor,
#             verb='VISIT',
#             target_id=instance.id
#         )

# @receiver(post_save, sender=Match)
# def create_match_notification(sender, instance, created, **kwargs):
#     try:
#         if created:
#             for user in [instance.user1, instance.user2]:
#                 Notification.objects.create(
#                     recipient=user,
#                     actor=instance.user2 if user == instance.user1 else instance.user1,
#                     verb='MATCH',
#                     target_id=instance.id
#                 )
#     except Exception as e:
#            print(f"Error creating notification: {str(e)}")
#         #    print(
#         #     f"Notification error for Like {instance.id}: "
#         #     f"Recipient: {instance.liked_id}, "
#         #     f"Actor: {instance.liker_id}, "
#         #     # f"Verb: {verb}, "
#         #     f"Error: {str(e)}",
#         #     exc_info=True
#         # )



# # @receiver(post_save, sender=Notification)
# # def broadcast_notification(sender, instance, created, **kwargs):
# #     if created:
# #         channel_layer = get_channel_layer()
# #         async_to_sync(channel_layer.group_send)(
# #               f'user_{instance.recipient.id}',
# #             # f'notifications_{instance.recipient.id}',
# #             {
# #                 'type': 'send_notification',
# #                 'content': {
# #                     'type': instance.verb,
# #                     'actor_id': instance.actor.id,
# #                     'message': f'New {instance.verb} from {instance.actor.username}',
# #                 }
# #             }
# #         )


# @receiver(post_save, sender=Notification)
# def broadcast_notification(sender, instance, created, **kwargs):
#     if created:
#         profile = instance.actor.profile
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)(
#               f'user_{instance.recipient.id}',
#             # f'notifications_{instance.recipient.id}',
#             {
#                 'type': 'send_notification',
#                 'content': {
#                     'type': instance.verb,
#                     'actor_id': instance.actor.id,
#                     'profile': {
#                         'id': instance.actor.id,
#                         'display_name': profile.display_name,
#                         'profile_photo': instance.actor.get_profile_photo()
#                     },
#                     'message': f'New {instance.verb} from {profile.display_name}',
#                 }
#             }
#         )