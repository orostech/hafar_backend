# views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return notifications for the logged-in user
        return self.queryset.filter(recipient=self.request.user).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        self.get_queryset().update(read=True)
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['GET'])
    def mark_all_read(self, request):
        """
        Mark all notifications as read for the current user.
        """
        updated = self.get_queryset().filter(read=False).update(read=True)
        return Response({
            'status': 'success',
            'message': f'{updated} notifications marked as read.'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['DELETE'])
    def clear_notifications(self, request):
        """
        Delete all notifications for the current user.
        """
        deleted, _ = self.get_queryset().delete()
        return Response({
            'status': 'success',
            'message': f'{deleted} notifications deleted.'
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['PATCH'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a specific notification as read.
        """
        notification = self.get_object()
        if not notification.read:
            notification.read = True
            notification.save()
        return Response({
            'status': 'success',
            'message': 'Notification marked as read.'
        }, status=status.HTTP_200_OK)