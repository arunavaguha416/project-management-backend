from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from attachments.models.attachment_model import Attachment
from attachments.serializers.attachment_serializer import AttachmentSerializer
from django.core.paginator import Paginator
import datetime

class AttachmentAdd(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data.copy()
            if 'file' in request.FILES:
                data['file'] = request.FILES['file']
                data['filename'] = request.FILES['file'].name
            serializer = AttachmentSerializer(data=data)
            if serializer.is_valid():
                serializer.save(uploader=request.user)
                return Response({
                    'status': True,
                    'message': 'Attachment added successfully',
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
                'message': 'An error occurred while adding the attachment',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class AttachmentList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_filename = search_data.get('filename', '')

            query = Q(uploader=request.user) | Q(related_object__project__owner=request.user) | Q(related_object__task__project__owner=request.user)
            if search_filename:
                query &= Q(filename__icontains=search_filename)

            attachments = Attachment.objects.filter(query).order_by('-created_at')

            if attachments.exists():
                if page is not None:
                    paginator = Paginator(attachments, page_size)
                    paginated_attachments = paginator.get_page(page)
                    serializer = AttachmentSerializer(paginated_attachments, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = AttachmentSerializer(attachments, many=True)
                    return Response({
                        'status': True,
                        'count': attachments.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Attachments not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PublishedAttachmentList(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            attachments = Attachment.objects.filter(published_at__isnull=False).values('id', 'filename').order_by('-created_at')
            if attachments.exists():
                return Response({
                    'status': True,
                    'records': attachments
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Attachments not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DeletedAttachmentList(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_filename = search_data.get('filename', '')

            query = Q(deleted_at__isnull=False)
            if search_filename:
                query &= Q(filename__icontains=search_filename)

            attachments = Attachment.all_objects.filter(query).order_by('-created_at')

            if attachments.exists():
                if page is not None:
                    paginator = Paginator(attachments, page_size)
                    paginated_attachments = paginator.get_page(page)
                    serializer = AttachmentSerializer(paginated_attachments, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = AttachmentSerializer(attachments, many=True)
                    return Response({
                        'status': True,
                        'count': attachments.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Deleted attachments not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class AttachmentDetails(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            attachment_id = request.data.get('id')
            if attachment_id:
                attachment = Attachment.objects.filter(
                    Q(id=attachment_id, uploader=request.user) | 
                    Q(id=attachment_id, related_object__project__project__owner=request.user) |
                    Q(id=attachment_id, related_object__task__project__owner=request.user)
                ).values('id', 'filename', 'file_url').first()
                if attachment:
                    return Response({
                        'status': True,
                        'records': attachment
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Attachment not found',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide an attachmentId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching attachment details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class AttachmentUpdate(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request):
        try:
            attachment_id = request.data.get('id')
            attachment = Attachment.objects.filter(id=attachment_id).first()
            if attachment:
                data = request.data.copy()
                if 'file' in request.FILES:
                    data['file'] = request.FILES['file']
                    data['filename'] = request.FILES['file'].name
                serializer = AttachmentSerializer(attachment, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'Attachment updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Attachment not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the attachment',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ChangeAttachmentPublishStatus(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request):
        try:
            attachment_id = request.data.get('id')
            publish = request.data.get('status')
            if publish == 1:
                data = {'published_at': datetime.datetime.now()}
            elif publish == 0:
                data = {'published_at': None}
            attachment = Attachment.objects.get(id=attachment_id)
            serializer = AttachmentSerializer(attachment, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Publish status updated successfully',
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Unable to update publish status',
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

class AttachmentDelete(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, attachment_id):
        try:
            attachment = Attachment.objects.filter(id=attachment_id).first()
            if attachment:
                attachment.soft_delete()
                return Response({
                    'status': True,
                    'message': 'Attachment deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Attachment not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RestoreAttachment(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            attachment_id = request.data.get('id')
            attachment = Attachment.all_objects.get(id=attachment_id)
            if attachment:
                attachment.deleted_at = None
                attachment.save()
                return Response({
                    'status': True,
                    'message': 'Attachment restored successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Attachment not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)