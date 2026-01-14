from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from projects.models.project_model import Project, ProjectFile
from projects.models.sprint_model import Sprint
from projects.models.task_model import Task
from projects.utils.permissions import require_project_viewer,require_project_manager_or_hr
from projects.utils.sprint_ai_utils import get_sprint_ai_explanation
from projects.models.sprint_ai_snapshot import SprintAISnapshot




class SprintAIExplanationView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get("sprint_id")

            sprint = Sprint.objects.select_related("project").filter(
                id=sprint_id,
                deleted_at__isnull=True
            ).first()

            if not sprint:
                return Response(
                    {"status": False, "message": "Sprint not found"},
                    status=200
                )

            # require_project_member(request.user, sprint.project)
            require_project_viewer(request.user, sprint.project)

            explanation = get_sprint_ai_explanation(sprint)
            SprintAISnapshot.objects.create(
                    sprint=sprint,
                    probability=explanation["final_probability"]
                )
            
            # Persist final probability (optional but recommended)
            sprint.ai_completion_probability = explanation["final_probability"]
            sprint.save(update_fields=["ai_completion_probability"])

            return Response({
                "status": True,
                "records": explanation
            }, status=200)

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=400
            )


class SprintAITrendView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        sprint_id = request.data.get("sprint_id")

        snapshots = SprintAISnapshot.objects.filter(
            sprint_id=sprint_id
        ).values("created_at", "probability")

        return Response({
            "status": True,
            "records": list(snapshots)
        })


class SprintAIPreview(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get("project_id")

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response(
                    {"status": False, "message": "Project not found"},
                    status=404
                )

            require_project_manager_or_hr(request.user, project)

            files = ProjectFile.objects.filter(project=project)

            # 🔥 Simulated AI logic (hook later)
            tasks = []
            for f in files:
                tasks.append({
                    "title": f"Review document: {f.original_name}",
                    "story_points": 3,
                    "priority": "MEDIUM"
                })

            return Response({
                "status": True,
                "records": {
                    "goal": "Initial sprint based on project documents",
                    "tasks": tasks
                }
            })

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=400
            )
        


class SprintAICommit(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get("project_id")
            tasks = request.data.get("tasks", [])
            goal = request.data.get("goal", "")

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response(
                    {"status": False, "message": "Project not found"},
                    status=404
                )

            require_project_manager_or_hr(request.user, project)

            sprint = Sprint.objects.create(
                project=project,
                name="AI Generated Sprint",
                goal=goal,
                status="PLANNED"
            )

            for t in tasks:
                Task.objects.create(
                    project=project,
                    sprint= None,
                    title=t.get("title"),
                    story_points=t.get("story_points", 1),
                    status="TODO"
                )

            return Response({
                "status": True,
                "message": "AI sprint created",
                "records": {
                    "sprint_id": str(sprint.id)
                }
            })

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=400
            )




