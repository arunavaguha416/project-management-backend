from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count
import os

from projects.models.project_model import Project, ProjectFile
from projects.models.project_model import Milestone
from projects.models.sprint_model import Sprint
from projects.models.task_model import Task
from projects.utils.permissions import require_project_viewer,require_project_manager_or_hr
from projects.utils.sprint_ai_utils import get_sprint_ai_explanation
from projects.utils.ollama_sprint_brief import build_sprint_brief, build_quick_brief
from projects.utils.ollama_client import ollama_generate, is_ollama_running
from projects.models.sprint_ai_snapshot import SprintAISnapshot
from requests.exceptions import Timeout




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


class SprintAIBriefView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get("sprint_id")
            cache_key = f"sprint_ai_brief:{sprint_id}"
            cached = cache.get(cache_key)
            if cached:
                return Response({
                    "status": True,
                    "records": cached,
                    "cached": True
                }, status=200)

            sprint = Sprint.objects.select_related("project").filter(
                id=sprint_id,
                deleted_at__isnull=True
            ).first()

            if not sprint:
                return Response(
                    {"status": False, "message": "Sprint not found"},
                    status=200
                )

            require_project_viewer(request.user, sprint.project)

            tasks = list(Task.objects.filter(sprint=sprint, deleted_at__isnull=True))
            quick_brief = build_quick_brief(sprint, tasks)
            try:
                brief = build_sprint_brief(sprint, tasks, fallback=quick_brief)
            except Exception:
                brief = quick_brief
            cache.set(cache_key, brief, timeout=300)

            return Response({
                "status": True,
                "records": brief
            }, status=200)

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=400
            )


class SprintAIChatView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get("sprint_id")
            message = request.data.get("message", "")

            sprint = Sprint.objects.select_related("project").filter(
                id=sprint_id,
                deleted_at__isnull=True
            ).first()

            if not sprint:
                return Response({"status": False, "message": "Sprint not found"}, status=200)

            require_project_viewer(request.user, sprint.project)

            msg = (message or "").lower()
            if "backlog" in msg and ("how many" in msg or "count" in msg or "cards" in msg):
                backlog_count = Task.objects.filter(
                    project=sprint.project,
                    sprint__isnull=True,
                    deleted_at__isnull=True
                ).count()
                return Response({
                    "status": True,
                    "records": {"reply": f"There are {backlog_count} backlog items for this project."}
                }, status=200)
            if "how many more" in msg or "more cards" in msg or "needed" in msg:
                total = Task.objects.filter(sprint=sprint, deleted_at__isnull=True).count()
                done = Task.objects.filter(sprint=sprint, status="DONE", deleted_at__isnull=True).count()
                remaining = max(total - done, 0)
                return Response({
                    "status": True,
                    "records": {"reply": f"There are {remaining} remaining task(s) in this sprint."}
                }, status=200)
            if "how many" in msg or "count" in msg:
                total = Task.objects.filter(sprint=sprint, deleted_at__isnull=True).count()
                if "blocked" in msg:
                    blocked = Task.objects.filter(sprint=sprint, status="BLOCKED", deleted_at__isnull=True).count()
                    return Response({"status": True, "records": {"reply": f"{blocked} task(s) are blocked in this sprint."}}, status=200)
                if "done" in msg or "completed" in msg:
                    done = Task.objects.filter(sprint=sprint, status="DONE", deleted_at__isnull=True).count()
                    return Response({"status": True, "records": {"reply": f"{done} task(s) are completed in this sprint."}}, status=200)
                if "in progress" in msg:
                    ip = Task.objects.filter(sprint=sprint, status="IN_PROGRESS", deleted_at__isnull=True).count()
                    return Response({"status": True, "records": {"reply": f"{ip} task(s) are in progress in this sprint."}}, status=200)
                if "board" in msg or "cards" in msg:
                    return Response({"status": True, "records": {"reply": f"There are {total} task card(s) on the sprint board."}}, status=200)
                return Response({"status": True, "records": {"reply": f"This sprint has {total} task(s) in total."}}, status=200)

            if not is_ollama_running():
                return Response({
                    "status": True,
                    "records": {
                        "reply": "Ollama is offline. Please start the Ollama service to use the AI helper."
                    }
                }, status=200)

            context_key = f"sprint_ai_context:{sprint_id}"
            context = cache.get(context_key)
            if not context:
                tasks = list(Task.objects.filter(sprint=sprint, deleted_at__isnull=True))
                total = len(tasks)
                done = sum(1 for t in tasks if (t.status or "").upper() == "DONE")
                blocked = sum(1 for t in tasks if (t.status or "").upper() == "BLOCKED")
                in_progress = sum(1 for t in tasks if (t.status or "").upper() == "IN_PROGRESS")
                overdue = 0
                now = timezone.now().date()
                for t in tasks:
                    due = getattr(t, "due_date", None)
                    if due:
                        if hasattr(due, "date"):
                            due = due.date()
                        if due < now and (t.status or "").upper() != "DONE":
                            overdue += 1

                task_lines = [
                    f"- {t.title} | status={t.status} | priority={t.priority} | assignee={getattr(t.assigned_to, 'name', 'Unassigned')}"
                    for t in tasks[:20]
                ]

                milestones = Milestone.objects.filter(project=sprint.project).values("title", "status", "target_date")[:8]
                milestone_lines = [
                    f"- {m['title']} | status={m['status']} | target={m['target_date'] or 'N/A'}"
                    for m in milestones
                ]

                def _read_snippet(path: str) -> str:
                    try:
                        ext = os.path.splitext(path or "")[1].lower()
                        if ext not in [".txt", ".md", ".csv", ".json"]:
                            return ""
                        if not os.path.exists(path):
                            return ""
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            return f.read(1800)
                    except Exception:
                        return ""

                files = ProjectFile.objects.filter(project=sprint.project).values("original_name", "file_path")[:4]
                doc_lines = []
                for f in files:
                    snippet = _read_snippet(f.get("file_path"))
                    if snippet:
                        doc_lines.append(f"- {f.get('original_name')} :: {snippet}")
                    else:
                        doc_lines.append(f"- {f.get('original_name')}")

                context = {
                    "project": {
                        "name": sprint.project.name,
                        "status": sprint.project.status,
                        "description": sprint.project.description or "N/A",
                        "start_date": str(sprint.project.start_date) if sprint.project.start_date else "N/A",
                        "end_date": str(sprint.project.end_date) if sprint.project.end_date else "N/A",
                    },
                    "sprint": {
                        "name": sprint.name,
                        "goal": sprint.goal or "N/A",
                        "status": sprint.status,
                        "start_date": str(sprint.start_date) if sprint.start_date else "N/A",
                        "end_date": str(sprint.end_date) if sprint.end_date else "N/A",
                        "stats": {
                            "total": total,
                            "done": done,
                            "in_progress": in_progress,
                            "blocked": blocked,
                            "overdue": overdue
                        }
                    },
                    "tasks": task_lines,
                    "milestones": milestone_lines,
                    "docs": doc_lines
                }
                cache.set(context_key, context, timeout=600)

            prompt = f"""
You are an expert agile sprint assistant. Answer the user's question about the sprint.
Be precise, action-oriented, and do not invent data. If the data is not available,
say so and suggest how to get it.

Project:
name: {context['project']['name']}
status: {context['project']['status']}
description: {context['project']['description']}
start_date: {context['project']['start_date']}
end_date: {context['project']['end_date']}

Sprint:
name: {context['sprint']['name']}
goal: {context['sprint']['goal']}
status: {context['sprint']['status']}
start_date: {context['sprint']['start_date']}
end_date: {context['sprint']['end_date']}
stats: total={context['sprint']['stats']['total']}, done={context['sprint']['stats']['done']},
in_progress={context['sprint']['stats']['in_progress']}, blocked={context['sprint']['stats']['blocked']},
overdue={context['sprint']['stats']['overdue']}

Tasks:
{chr(10).join(context['tasks'])}

Milestones:
{chr(10).join(context['milestones'])}

Uploaded docs (snippets if text):
{chr(10).join(context['docs'])}

User question:
{message}
"""

            try:
                reply = ollama_generate(prompt, timeout=8)
            except Timeout:
                stats = context["sprint"]["stats"]
                return Response({
                    "status": True,
                    "records": {
                        "reply": (
                            f"Quick sprint snapshot: total {stats['total']}, done {stats['done']}, "
                            f"in progress {stats['in_progress']}, blocked {stats['blocked']}, overdue {stats['overdue']}. "
                            "Ask a specific question for deeper analysis."
                        )
                    }
                }, status=200)

            return Response({
                "status": True,
                "records": {"reply": reply.strip() or "No response"}
            }, status=200)

        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=400)


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




