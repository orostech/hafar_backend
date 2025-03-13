from django.utils import timezone
from django.conf import settings
from users.models import Profile

class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            should_update = False
            if hasattr(request.user, 'profile'):
                last_seen = request.user.profile.last_seen
                if not last_seen or (timezone.now() - last_seen) > timezone.timedelta(minutes=10):
                    should_update = True
            if should_update:
                Profile.objects.filter(user=request.user).update(last_seen=timezone.now())

        return response
