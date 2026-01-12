from projects.utils.sprint_capacity_service import calculate_sprint_capacity


def generate_sprint_plan(sprint, backlog_tasks):
    capacity = calculate_sprint_capacity(sprint)

    assignees = {
        a["employee_id"]: {
            **a,
            "used": 0
        }
        for a in capacity["assignees"]
        if a["leave_days"] == 0
    }

    suggestions = []
    skipped = []

    for task in backlog_tasks:
        best_assignee = None
        best_ratio = 1e9

        for emp_id, a in assignees.items():
            remaining = a["capacity_points"] - a["used"]
            if remaining >= (task.story_points or 0):
                ratio = a["used"] / max(a["capacity_points"], 1)
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_assignee = emp_id

        if best_assignee:
            assignees[best_assignee]["used"] += task.story_points or 0
            suggestions.append({
                "task_id": str(task.id),
                "assign_to": best_assignee,
                "story_points": task.story_points
            })
        else:
            skipped.append(str(task.id))

    return {
        "suggested_tasks": suggestions,
        "skipped_tasks": skipped,
        "capacity_used": sum(a["used"] for a in assignees.values())
    }
