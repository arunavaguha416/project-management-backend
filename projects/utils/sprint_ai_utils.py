from datetime import date
from projects.models.task_model import Task


def calculate_sprint_ai_completion(sprint):
    """
    Calculate AI completion probability for a sprint (0–100)
    """

    tasks = Task.objects.filter(
        sprint=sprint,
        deleted_at__isnull=True
    )

    total_tasks = tasks.count()
    if total_tasks == 0:
        return 0

    total_sp = sum(t.story_points or 0 for t in tasks)
    completed_sp = sum(
        t.story_points or 0
        for t in tasks
        if t.status == "DONE"
    )

    # 1️⃣ Completion score
    completion_ratio = completed_sp / total_sp if total_sp > 0 else 0
    completion_score = completion_ratio * 100

    # 2️⃣ Schedule efficiency
    if sprint.start_date and sprint.end_date:
        today = date.today()
        elapsed_days = max((today - sprint.start_date).days, 1)
        total_days = max((sprint.end_date - sprint.start_date).days, 1)

        time_ratio = elapsed_days / total_days
        schedule_efficiency = completion_ratio / time_ratio if time_ratio > 0 else 0
        schedule_score = min(schedule_efficiency, 1.2) * 100
    else:
        schedule_score = 50  # neutral if dates missing

    # 3️⃣ Velocity health
    if sprint.velocity > 0:
        velocity_ratio = completed_sp / sprint.velocity
        velocity_score = min(velocity_ratio, 1) * 100
    else:
        velocity_score = 50  # neutral

    # 4️⃣ Blocker penalty
    blocked_tasks = tasks.filter(status="BLOCKED").count()
    blocker_ratio = blocked_tasks / total_tasks
    blocker_score = 100 - (blocker_ratio * 100)

    # Final weighted score
    ai_probability = (
        0.4 * completion_score +
        0.3 * schedule_score +
        0.2 * velocity_score +
        0.1 * blocker_score
    )

    return round(max(0, min(ai_probability, 100)))


def get_sprint_ai_explanation(sprint):
    """
    Returns detailed explainability for AI completion probability
    """

    tasks = Task.objects.filter(
        sprint=sprint,
        deleted_at__isnull=True
    )

    total_tasks = tasks.count()
    blocked_tasks = tasks.filter(status="BLOCKED").count()

    total_sp = sum(t.story_points or 0 for t in tasks)
    completed_sp = sum(
        t.story_points or 0
        for t in tasks
        if t.status == "DONE"
    )

    # ---------------------------------------------------
    # Completion signal (40%)
    # ---------------------------------------------------
    completion_ratio = completed_sp / total_sp if total_sp > 0 else 0
    completion_score = round(completion_ratio * 100)

    # ---------------------------------------------------
    # Schedule signal (30%)
    # ---------------------------------------------------
    time_ratio = None
    if sprint.start_date and sprint.end_date:
        today = date.today()
        elapsed_days = max((today - sprint.start_date).days, 1)
        total_days = max((sprint.end_date - sprint.start_date).days, 1)

        time_ratio = elapsed_days / total_days
        schedule_efficiency = completion_ratio / time_ratio if time_ratio > 0 else 0
        schedule_score = round(min(schedule_efficiency, 1.2) * 100)
    else:
        schedule_score = 50  # neutral if dates missing

    # ---------------------------------------------------
    # Velocity signal (20%)
    # ---------------------------------------------------
    velocity_ratio = None
    if sprint.velocity and sprint.velocity > 0:
        velocity_ratio = completed_sp / sprint.velocity
        velocity_score = round(min(velocity_ratio, 1) * 100)
    else:
        velocity_score = 50  # neutral

    # ---------------------------------------------------
    # Blocker signal (10%)
    # ---------------------------------------------------
    blocker_ratio = blocked_tasks / total_tasks if total_tasks > 0 else 0
    blocker_score = round(100 - (blocker_ratio * 100))

    # ---------------------------------------------------
    # Final weighted probability
    # ---------------------------------------------------
    final_probability = round(
        (0.4 * completion_score) +
        (0.3 * schedule_score) +
        (0.2 * velocity_score) +
        (0.1 * blocker_score)
    )

    final_probability = max(0, min(final_probability, 100))

    # ---------------------------------------------------
    # Human-readable summary
    # ---------------------------------------------------
    if final_probability >= 75:
        summary = "Sprint is on track with a high likelihood of completion"
    elif final_probability >= 50:
        summary = "Sprint progress is moderate but requires attention"
    else:
        summary = "Sprint is at risk and may not complete on time"

    # ---------------------------------------------------
    # Improvement hints
    # ---------------------------------------------------
    hints = []

    if completion_score < 50:
        hints.append("Complete more story points to increase progress")

    if schedule_score < 50:
        hints.append("Sprint is behind schedule — consider reprioritizing tasks")

    if velocity_score < 50:
        hints.append("Planned velocity may be unrealistic or work is blocked")

    if blocker_score < 80:
        hints.append("Resolve blocked tasks to reduce risk")

    if not hints:
        hints.append("Sprint is healthy — maintain the current pace")

    # ---------------------------------------------------
    # Final payload
    # ---------------------------------------------------
    return {
        "final_probability": final_probability,
        "summary": summary,
        "hints": hints,
        "signals": {
            "completion": {
                "score": completion_score,
                "completed_story_points": completed_sp,
                "total_story_points": total_sp,
                "weight": 40,
                "message": "Based on completed work"
            },
            "schedule": {
                "score": schedule_score,
                "time_elapsed_ratio": time_ratio,
                "weight": 30,
                "message": "Progress compared to elapsed sprint time"
            },
            "velocity": {
                "score": velocity_score,
                "planned_velocity": sprint.velocity,
                "weight": 20,
                "message": "Planned vs achieved capacity"
            },
            "blockers": {
                "score": blocker_score,
                "blocked_tasks": blocked_tasks,
                "weight": 10,
                "message": "Penalty for blocked tasks"
            }
        }
    }