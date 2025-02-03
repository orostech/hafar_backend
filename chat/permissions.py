from rest_framework import permissions


def has_chat_permission(user, chat):
    return user in [chat.user1, chat.user2] and chat.is_active

class ChatPermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_chat_permission(request.user, obj)

# # Apply to views
# class ChatViewSet(viewsets.ModelViewSet):
#     permission_classes = [permissions.IsAuthenticated, ChatPermissions]