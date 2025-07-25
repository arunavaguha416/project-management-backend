from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from notifications.models.notification_model import Notification
from notifications.serializers.notification_serializer import NotificationSerializer
from django.core.paginator import Paginator
import datetime

class NotificationAdd(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            serializer = NotificationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Notification added successfully',
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while adding the notification',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class NotificationList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_message = search_data.get('message', '')
            search_is_read = search_data.get('is_read', None)

            query = Q(recipient=request.user)
            if search_message:
                query &= Q(message__icontains=search_message)
            if search_is_read is not None:
                query &= Q(is_read=search_is_read)

            notifications = Notification.objects.filter(query).order_by('-created_at')

            if notifications.exists():
                if page is not None:
                    paginator = Paginator(notifications, page_size)
                    paginated_notifications = paginator.get_page(page)
                    serializer = NotificationSerializer(paginated_notifications, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = NotificationSerializer(notifications, many=True)
                    return Response({
                        'status': True,
                        'count': notifications.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Notifications not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DeletedNotificationList(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_message = search_data.get('message', '')

            query = Q(deleted_at__isnull=False)
            if search_message:
                query &= Q(message__icontains=search_message)

            notifications = Notification.all_objects.filter(query).order_by('-created_at')

            if notifications.exists():
                if page is not None:
                    paginator = Paginator(notifications, page_size)
                    paginated_notifications = paginator.get_page(page)
                    serializer = NotificationSerializer(paginated_notifications, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = NotificationSerializer(notifications, many=True)
                    return Response({
                        'status': True,
                        'count': notifications.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Deleted notifications not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class NotificationDetails(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            notification_id = request.data.get('id')
            if notification_id:
                notification = Notification.objects.filter(
                    id=notification_id, recipient=request.user
                ).values('id', 'message', 'notification_type', 'is_read').first()
                if notification:
                    return Response({
                        'status': True,
                        'records': notification
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Notification not found',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide notificationId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching notification details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class NotificationUpdate(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request):
        try:
            notification_id = request.data.get('id')
            notification = Notification.objects.filter(id=notification_id).first()
            if notification:
                serializer = NotificationSerializer(notification, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'Notification updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Notification not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the notification',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class MarkNotificationRead(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            notification_id = request.data.get('id')
            notification = Notification.objects.filter(id=notification_id, recipient=request.user).first()
            if notification:
                notification.is_read = True
                notification.save()
                return Response({
                    'status': True,
                    'message': 'Notification marked as read'
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Notification not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)