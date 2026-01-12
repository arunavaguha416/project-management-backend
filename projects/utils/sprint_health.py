from datetime import date
import math
from statistics import mean, pstdev

# -----------------------------
# Completion Health (0–30)
# -----------------------------
def completion_score(completed_sp, total_sp, elapsed_days, total_days):
    if total_sp == 0 or elapsed_days == 0:
        return 30

    expected = elapsed_days / total_days
    actual = completed_sp / total_sp
    ratio = actual / expected if expected else 0

    if ratio >= 1.0:
        return 30
    if ratio >= 0.9:
        return 26
    if ratio >= 0.75:
        return 20
    if ratio >= 0.5:
        return 12
    return 5


# -----------------------------
# Scope Stability (0–20)
# -----------------------------
def scope_score(added, removed, original):
    if original == 0:
        return 20

    ratio = (added + removed) / original

    if ratio <= 0.05:
        return 20
    if ratio <= 0.10:
        return 16
    if ratio <= 0.20:
        return 10
    if ratio <= 0.30:
        return 5
    return 0


# -----------------------------
# Flow Health (0–20)
# -----------------------------
def flow_score(avg_cycle, avg_lead):
    if not avg_lead or avg_lead == 0:
        return 20

    efficiency = avg_cycle / avg_lead

    if efficiency >= 0.7:
        return 20
    if efficiency >= 0.5:
        return 15
    if efficiency >= 0.35:
        return 10
    if efficiency >= 0.2:
        return 5
    return 0


# -----------------------------
# WIP Discipline (0–15)
# -----------------------------
def wip_score(violations):
    if violations == 0:
        return 15
    if violations <= 2:
        return 12
    if violations <= 5:
        return 8
    if violations <= 8:
        return 4
    return 0


# -----------------------------
# Workload Balance (0–15)
# -----------------------------
def workload_score(points_per_user):
    if len(points_per_user) <= 1:
        return 15

    avg = mean(points_per_user)
    if avg == 0:
        return 15

    cv = pstdev(points_per_user) / avg

    if cv <= 0.25:
        return 15
    if cv <= 0.4:
        return 10
    if cv <= 0.6:
        return 6
    return 2
