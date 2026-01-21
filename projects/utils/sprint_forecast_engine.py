from hr_management.utils.hr_sprint_forecasting import *

def generate_sprint_forecast(project, sprint=None):
    """
    HR-driven sprint risk prediction
    """

    score = 100
    reasons = []

    # ---------------- HR DATA ----------------
    employees = get_project_employees(project)
    leave_ratio = calculate_leave_ratio(employees)

    if leave_ratio > 0.2:
        score -= 20
        reasons.append("High team leave during sprint window")

    if is_manager_on_leave(project):
        score -= 25
        reasons.append("Project manager unavailable")

    overtime = calculate_avg_overtime(employees)
    if overtime > 15:
        score -= 10
        reasons.append("Team overtime burnout risk")

    attendance = calculate_attendance_score(employees)
    if attendance < 90:
        score -= 15
        reasons.append("Low team attendance trend")

    # ---------------- SPRINT DATA ----------------
    if sprint:
        if sprint.ai_completion_probability < 60:
            score -= 20
            reasons.append("Low AI completion confidence")

        if is_over_capacity(sprint):
            score -= 30
            reasons.append("Sprint overloaded")

    score = max(0, min(score, 100))

    return {
        "forecast_score": score,
        "risk_level": get_risk_label(score),
        "reasons": reasons[:4]  # keep it sharp
    }
