from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from django.core.paginator import Paginator

from projects.models.comments_model import Comment
from projects.models.task_model import Task
from projects.serializers.comment_serializer import CommentSerializer
from projects.utils.permissions import (
    require_project_viewer,
    require_project_owner,
)


# ------------------------------------------------------------------
# Add Comment
# ------------------------------------------------------------------
class CommentAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            task_id = request.data.get('task')
            task = Task.objects.select_related('project').filter(id=task_id).first()

            if not task:
                return Response(
                    {'status': False, 'message': 'Task not found'},
                    status=status.HTTP_200_OK
                )

            # 🔐 membership guard
            require_project_viewer(request.user, task.project)

            data = request.data.copy()
            data['comment_by_id'] = request.user.id

            serializer = CommentSerializer(data=data)
            if serializer.is_valid():
                serializer.save(comment_by=request.user)
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
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------------------------------------------
# List Comments
# ------------------------------------------------------------------
class CommentList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            task_id = request.data.get('task_id')
            if not task_id:
                return Response(
                    {'status': False, 'message': 'task_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            task = Task.objects.select_related('project').filter(id=task_id).first()
            if not task:
                return Response(
                    {'status': False, 'message': 'Task not found'},
                    status=status.HTTP_200_OK
                )

            # 🔐 membership guard
            require_project_viewer(request.user, task.project)

            comments = Comment.objects.filter(
                task=task,
                deleted_at__isnull=True
            ).order_by('-created_at')

            serializer = CommentSerializer(comments, many=True)

            return Response({
                'status': True,
                'count': comments.count(),
                'records': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------------------------------------------
# Comment Details  ✅ FIXED HERE
# ------------------------------------------------------------------
class CommentDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, comment_id):
        try:
            comment = Comment.objects.select_related(
                'task__project'
            ).filter(id=comment_id).first()

            if not comment:
                return Response(
                    {'status': False, 'message': 'Comment not found'},
                    status=status.HTTP_200_OK
                )

            # 🔐 FIX: ProjectMember-based access (not project.owner)
            require_project_viewer(request.user, comment.task.project)

            serializer = CommentSerializer(comment)
            return Response(
                {'status': True, 'records': serializer.data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------------------------------------------
# Delete Comment
# ------------------------------------------------------------------
class CommentDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, comment_id):
        try:
            comment = Comment.objects.select_related(
                'task__project'
            ).filter(id=comment_id).first()

            if not comment:
                return Response(
                    {'status': False, 'message': 'Comment not found'},
                    status=status.HTTP_200_OK
                )

            # 🔐 only OWNER can delete comments
            require_project_owner(request.user, comment.task.project)

            comment.soft_delete()
            return Response(
                {'status': True, 'message': 'Comment deleted successfully'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------------------------------------------
# Restore Comment (ADMIN ONLY – unchanged behavior)
# ------------------------------------------------------------------
class RestoreComment(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            comment = Comment.all_objects.filter(
                id=request.data.get('id')
            ).first()

            if not comment:
                return Response(
                    {'status': False, 'message': 'Comment not found'},
                    status=status.HTTP_200_OK
                )

            comment.deleted_at = None
            comment.save()

            return Response(
                {'status': True, 'message': 'Comment restored successfully'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
