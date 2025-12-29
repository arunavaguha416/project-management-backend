# hr_management/utils/attendance_utils.py

from datetime import date, timedelta, datetime
from calendar import monthrange

def calculate_working_days(year, month):
    total_days = monthrange(year, month)[1]
    working_days = 0

    for day in range(1, total_days + 1):
        d = date(year, month, day)
        if d.weekday() < 5:  # Mon–Fri
            working_days += 1

    return working_days


def calculate_overtime_hours(attendances):
    overtime = 0.0

    for a in attendances:
        if a.in_time and a.out_time:
            worked_seconds = (
                datetime.combine(date.today(), a.out_time)
                - datetime.combine(date.today(), a.in_time)
            ).seconds

            worked_hours = worked_seconds / 3600

            if worked_hours > 8:
                overtime += worked_hours - 8

    return round(overtime, 2)
