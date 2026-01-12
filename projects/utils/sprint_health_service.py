from django.utils import timezone
from django.db.models import Sum, Count
from projects.models.task_model import Task, TaskStatusHistory
from projects.utils.sprint_health import *
from datetime import date

def calculate_sprint_health(sprint):
    today = timezone.now().date()

    # -----------------------------------
    # SAFE DATE NORMALIZATION (FIX)
    # -----------------------------------
    start_date = sprint.start_date or today

    # If sprint is completed, end_date exists
    # Otherwise, assume today
    end_date = sprint.end_date or today

    total_days = max((end_date - start_date).days + 1, 1)
    elapsed_days = max((today - start_date).days + 1, 1)
    elapsed_days = min(elapsed_days, total_days)

    tasks = Task.objects.filter(
        sprint=sprint,
        deleted_at__isnull=True
    )

    # ---------------- Completion ----------------
    total_sp = tasks.aggregate(total=Sum('story_points'))['total'] or 0
    completed_sp = tasks.filter(status='DONE').aggregate(
        total=Sum('story_points')
    )['total'] or 0

    completion = completion_score(
        completed_sp, total_sp, elapsed_days, total_days
    )

    # ---------------- Scope ----------------
    original_count = tasks.count()

    added = TaskStatusHistory.objects.filter(
        task__sprint=sprint,
        from_status__isnull=True
    ).count()

    removed = TaskStatusHistory.objects.filter(
        task__sprint=sprint,
        to_status__isnull=True
    ).count()


    scope = scope_score(added, removed, original_count)

    # ---------------- Flow ----------------
    cycle_times = []
    lead_times = []

    for task in tasks:
        history = TaskStatusHistory.objects.filter(task=task).order_by('changed_at')

        start = history.filter(to_status='IN_PROGRESS').first()
        done = history.filter(to_status='DONE').first()

        if start and done:
            cycle_times.append((done.changed_at - start.changed_at).days)

        lead_times.append((timezone.now() - task.created_at).days)

    avg_cycle = sum(cycle_times) / len(cycle_times) if cycle_times else 0
    avg_lead = sum(lead_times) / len(lead_times) if lead_times else 0

    flow = flow_score(avg_cycle, avg_lead)

    # ---------------- WIP ----------------
    wip_violations = 0  # v1 placeholder
    wip = wip_score(wip_violations)

    # ---------------- Workload ----------------
    rows = tasks.values('assigned_to').annotate(
        sp=Sum('story_points')
    )
    points = [r['sp'] or 0 for r in rows]
    workload = workload_score(points)

    total = completion + scope + flow + wip + workload

    return {
        'score': total,
        'breakdown': {
            'completion': completion,
            'scope': scope,
            'flow': flow,
            'wip': wip,
            'workload': workload
        },
        'raw': {
            'completed_sp': completed_sp,
            'total_sp': total_sp,
            'added': added,
            'removed': removed
        }
    }
