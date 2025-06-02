from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from comments.models.comment_model import Comment
from comments.serializers.comment_serializer import CommentSerializer
from django.core.paginator import Paginator
import datetime

class CommentAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(author=request.user)
                return Response({
                    'status': True,
                    'message': 'Comment added successfully',
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
                'message': 'An error occurred while adding the comment',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class CommentList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_content = search_data.get('content', '')

            query = Q(project__owner=request.user) | Q(task__project__owner=request.user)
            if search_content:
                query &= Q(content__icontains=search_content)

            comments = Comment.objects.filter(query).order_by('-created_at')

            if comments.exists():
                if page is not None:
                    paginator = Paginator(comments, page_size)
                    paginated_comments = paginator.get_page(page)
                    serializer = CommentSerializer(paginated_comments, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = CommentSerializer(comments, many=True)
                    return Response({
                        'status': True,
                        'count': comments.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Comments not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PublishedCommentList(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            comments = Comment.objects.filter(published_at__isnull=False).values('id', 'content').order_by('-created_at')
            if comments.exists():
                return Response({
                    'status': True,
                    'records': comments
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Comments not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DeletedCommentList(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_content = search_data.get('content', '')

            query = Q(deleted_at__isnull=False)
            if search_content:
                query &= Q(content__icontains=search_content)

            comments = Comment.all_objects.filter(query).order_by('-created_at')

            if comments.exists():
                if page is not None:
                    paginator = Paginator(comments, page_size)
                    paginated_comments = paginator.get_page(page)
                    serializer = CommentSerializer(paginated_comments, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = CommentSerializer(comments, many=True)
                    return Response({
                        'status': True,
                        'count': comments.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Deleted comments not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class CommentDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            comment_id = request.data.get('id')
            if comment_id:
                comment = Comment.objects.filter(
                    id=comment_id, project__owner=request.user
                ).values('id', 'content').first() or Comment.objects.filter(
                    id=comment_id, task__project__owner=request.user
                ).values('id', 'content').first()
                if comment:
                    return Response({
                        'status': True,
                        'records': comment
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Comment not found',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide commentId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching comment details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class CommentUpdate(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request):
        try:
            comment_id = request.data.get('id')
            comment = Comment.objects.filter(id=comment_id).first()
            if comment:
                serializer = CommentSerializer(comment, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'Comment updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Comment not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the comment',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ChangeCommentPublishStatus(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request):
        try:
            comment_id = request.data.get('id')
            publish = request.data.get('status')
            if publish == 1:
                data = {'published_at': datetime.datetime.now()}
            elif publish == 0:
                data = {'published_at': None}
            comment = Comment.objects.get(id=comment_id)
            serializer = CommentSerializer(comment, data=data, partial=True)
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

class CommentDelete(APIView):
    permission_classes = (IsAdminUser,)

    def delete(self, request, comment_id):
        try:
            comment = Comment.objects.filter(id=comment_id).first()
            if comment:
                comment.soft_delete()
                return Response({
                    'status': True,
                    'message': 'Comment deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Comment not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RestoreComment(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            comment_id = request.data.get('id')
            comment = Comment.all_objects.get(id=comment_id)
            if comment:
                comment.deleted_at = None
                comment.save()
                return Response({
                    'status': True,
                    'message': 'Comment restored successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Comment not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)