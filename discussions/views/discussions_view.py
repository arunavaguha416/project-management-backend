from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from discussions.models.discussions_model import Discussion
from discussions.serializers.discussions_serializer import DiscussionSerializer
from django.core.paginator import Paginator
import datetime

class DiscussionAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            serializer = DiscussionSerializer(data=request.data)
            if serializer.is_valid():
                discussion = serializer.save(creator=self.request.user)
                participant_ids = request.data.get('participant_ids', [])
                if participant_ids:
                    discussion.participants.set(participant_ids)
                return Response({
                    'status': True,
                    'message': 'Discussion added successfully',
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
                'message': 'An error occurred while adding the discussion',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DiscussionList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_title = search_data.get('title', 'search_title')
            search_content = search_data.get('content', '')

            query = Q(project__owner=request.user) | Q(participants=request.user)
            if search_title:
                query &= Q(title__icontains=search_title)
            if search_content:
                query &= Q(content__icontains=search_content)

            discussions = Discussion.objects.filter(query).order_by('-created_at')

            if discussions.exists():
                if page is not None:
                    paginator = Paginator(discussions, page_size)
                    paginated_discussions = paginator.get_page(page)
                    serializer = DiscussionSerializer(paginated_discussions, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = DiscussionSerializer(discussions, many=True)
                    return Response({
                        'status': True,
                        'count': discussions.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Discussions not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PublishedDiscussionList(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            discussions = Discussion.objects.filter(published_at__isnull=False).values('id', 'title').order_by('-created_at')
            if discussions.exists():
                return Response({
                    'status': True,
                    'records': discussions
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Discussions not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DeletedDiscussionList(APIView):
    permission_classes= (IsAdminUser,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)            
            search_title = search_data.get('title', '')
            search_content = search_data.get('content', '')

            query = Q(deleted_at__isnull=False)
            if search_title:
                query &= Q(title__icontains=search_title)
            if search_content:
                query &= Q(content__icontains=search_content)

            discussions = Discussion.all_objects.filter(query).order_by('-created_at')

            if discussions.exists():
                if page is not None:
                    paginator = Paginator(discussions, page_size)
                    paginated_discussions = paginator.get_page(page)
                    serializer = DiscussionSerializer(paginated_discussions, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = DiscussionSerializer(discussions, many=True)
                    return Response({
                        'status': True,
                        'count': discussions.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Deleted discussions not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DiscussionDetails(APIView):
    permission_classes= (IsAuthenticated,)

    def post(self, request):
        try:
            discussion_id = request.data.get('id')
            if discussion_id:
                discussion = Discussion.objects.filter(
                    id=discussion_id,project__owner=request.user).values('id', 'title', 'content').first()
                if discussion:
                    return Response({
                        'status': True,
                        'records': discussion
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Discussion not found',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide discussionId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching discussion details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DiscussionUpdate(APIView):
    permission_classes= (IsAdminUser,)

    def put(self, request):
        try:
            discussion_id = request.data.get('id')
            discussion = Discussion.objects.filter(id=discussion_id).first()
            if discussion:
                serializer = DiscussionSerializer(discussion, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    if 'participant_ids' in request.data:
                        discussion.participants.set(request.data.get('participant_ids', []))
                    return Response({
                        'status': True,
                        'message': 'Discussion updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Discussion not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the discussion',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ChangeDiscussionPublishStatus(APIView):
    permission_classes= (IsAdminUser,)

    def put(self, request):
        try:
            discussion_id = request.data.get('id')
            publish = request.data.get('status')
            if publish == 1:
                data = {'published_at': datetime.datetime.now()}
            elif publish == 0:
                data = {'published_at': None}
            discussion = Discussion.objects.get(id=discussion_id)
            serializer = DiscussionSerializer(discussion, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Publish status updated successfully',
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Unable to update publish status',
            }, status=status.HTTP_400_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

class DiscussionDelete(APIView):
    permission_classes= (IsAdminUser,)

    def delete(self, request, discussion_id):
        try:
            discussion = Discussion.objects.filter(id=discussion_id).first()
            if discussion:
                discussion.soft_delete()
                return Response({
                    'status': True,
                    'message': 'Discussion deleted successfully'
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Discussion not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_REQUEST)

class RestoreDiscussion(APIView):
    permission_classes= (IsAdminUser,)

    def post(self, request):
        try:
            discussion_id = request.data.get('id')
            discussion = Discussion.all_objects.get(id=discussion_id)
            if discussion:
                discussion.deleted_at = None
                discussion.save()
                return Response({
                    'status': True,
                    'message': 'Discussion restored successfully'
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Discussion not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_REQUEST)