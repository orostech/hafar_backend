# # middleware.py
# from django.utils import timezone
# from django.conf import settings

# class UpdateLastSeenMiddleware:
#     def __init__(self, get_response):
#         self.get_response = response

#     def __call__(self, request):
#         response = self.get_response(request)
        
#         if request.user.is_authenticated:
#             # Update last_seen less frequently to reduce database writes
#             should_update = False
            
#             if hasattr(request.user, 'profile'):
#                 last_seen = request.user.profile.last_seen
#                 # Only update if more than 5 minutes have passed
#                 if not last_seen or (timezone.now() - last_seen) > timezone.timedelta(minutes=10):
#                     should_update = True
                
#                 if should_update:
#                     request.user.profile.last_seen = timezone.now()
#                     # Use update() to avoid updating other fields
#                     request.user.profile.__class__.objects.filter(
#                         id=request.user.profile.id
#                     ).update(last_seen=timezone.now())
        
#         return response

