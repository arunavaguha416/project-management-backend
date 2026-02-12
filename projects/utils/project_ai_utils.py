from datetime import date

from projects.models.task_model import Task
from projects.models.sprint_model import Sprint
from projects.utils.sprint_ai_utils import calculate_sprint_ai_completion


def calculate_project_health(project):
    """
    Lightweight "AI" health score for a project (0-100).
    Uses task progress, blockers, overdue tasks, and active sprint health.
    """
    tasks = Task.objects.filter(project=project, deleted_at__isnull=True)
    total = tasks.count()

    if total == 0:
        return {
            "score": 50,
            "label": "Unknown",
            "reasons": ["No tasks created yet"],
            "signals": {
                "total": 0,
                "done": 0,
                "blocked": 0,
                "overdue": 0,
                "active_sprint_health": None,
            }
        }

    done = tasks.filter(status="DONE").count()
    blocked = tasks.filter(status="BLOCKED").count()
    overdue = tasks.filter(
        due_date__lt=date.today()
    ).exclude(status="DONE").count()

    progress_score = round((done / total) * 100)
    blocker_penalty = round((blocked / total) * 30)
    overdue_penalty = round((overdue / total) * 30)

    active_sprint = Sprint.objects.filter(
        project=project,
        status="ACTIVE",
        deleted_at__isnull=True
    ).first()

    sprint_health = None
    if active_sprint:
        sprint_health = calculate_sprint_ai_completion(active_sprint)

    base_score = max(0, 100 - blocker_penalty - overdue_penalty)
    if sprint_health is None:
        score = round((0.6 * progress_score) + (0.4 * base_score))
    else:
        score = round((0.4 * progress_score) + (0.3 * base_score) + (0.3 * sprint_health))

    score = max(0, min(score, 100))

    if score >= 80:
        label = "Healthy"
    elif score >= 60:
        label = "Watch"
    elif score >= 40:
        label = "At Risk"
    else:
        label = "Critical"

    reasons = []
    if progress_score < 40:
        reasons.append("Low completion rate")
    if blocked / total >= 0.2:
        reasons.append("High number of blocked tasks")
    if overdue / total >= 0.2:
        reasons.append("Overdue work piling up")
    if sprint_health is not None and sprint_health < 60:
        reasons.append("Active sprint is behind")
    if not reasons:
        reasons.append("Momentum looks good")

    return {
        "score": score,
        "label": label,
        "reasons": reasons[:3],
        "signals": {
            "total": total,
            "done": done,
            "blocked": blocked,
            "overdue": overdue,
            "active_sprint_health": sprint_health,
        }
    }
