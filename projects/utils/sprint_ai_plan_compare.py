# projects/utils/sprint_ai_plan_compare.py

def compare_plans(manual, ai):
    """
    Compare manually planned sprint vs AI suggested sprint.
    Returns risk and confidence delta.
    """

    manual_capacity = manual.get("capacity_used", 0)
    ai_capacity = ai.get("capacity_used", 0)

    manual_overloads = manual.get("overloaded_users", [])
    ai_overloads = ai.get("overloaded_users", [])

    return {
        "manual": {
            "capacity_used": manual_capacity,
            "overloads": len(manual_overloads),
            "risk": "HIGH" if manual_capacity > 100 or manual_overloads else "MEDIUM"
        },
        "ai": {
            "capacity_used": ai_capacity,
            "overloads": len(ai_overloads),
            "risk": "LOW"
        },
        "confidence_delta": ai_capacity - manual_capacity
    }
