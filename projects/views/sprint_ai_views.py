from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from projects.models.sprint_model import Sprint
from projects.utils.permissions import require_project_viewer
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
