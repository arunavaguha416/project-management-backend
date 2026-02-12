import os
import re
import hashlib
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from requests.exceptions import Timeout

from authentication.models.user import User
from hr_management.models.hr_management_models import Employee, LeaveRequest, LeaveBalance, Attendance
from payroll.models.payroll_models import PayRun, PayrollPeriod
from projects.models.project_model import Project, ManagerMapping, ProjectFile
from projects.models.sprint_model import Sprint
from projects.models.task_model import Task
from projects.utils.ollama_client import ollama_generate, is_ollama_running


class GlobalAIChatView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user = request.user
            role = (user.role or "USER").upper()
            message = request.data.get("message", "") or ""
            history = request.data.get("history", []) or []

            msg = message.lower()

            def _match_employee_from_message(text: str):
                employees = Employee.objects.filter(deleted_at__isnull=True).select_related("user", "department")
                for emp in employees:
                    if not emp.user or not emp.user.name:
                        continue
                    name = emp.user.name.lower()
                    tokens = [t for t in name.split() if t]
                    if all(t in text for t in tokens):
                        return emp
                    if name in text:
                        return emp
                return None

            # TTL-based caching per user + question (30 min)
            def _qkey(text: str) -> str:
                clean = re.sub(r"\s+", " ", (text or "").strip().lower())
                digest = hashlib.sha256(clean.encode("utf-8")).hexdigest()[:16]
                return f"ai:global:{user.id}:{role}:{digest}"

            cache_key = _qkey(message)
            cached = cache.get(cache_key)
            if cached:
                return Response({"status": True, "records": {"reply": cached, "cached": True}}, status=200)

            # Quick deterministic answers for common counts
            if "how many" in msg or "count" in msg:
                if "sprint" in msg and ("running" in msg or "active" in msg):
                    active_sprints = Sprint.objects.filter(status="ACTIVE", deleted_at__isnull=True)
                    sprint_count = active_sprints.count()
                    project_count = active_sprints.values_list("project_id", flat=True).distinct().count()
                    return Response(
                        {
                            "status": True,
                            "records": {
                                "reply": f"There are {sprint_count} active sprint(s) across {project_count} project(s)."
                            },
                        },
                        status=200,
                    )
                if "employee" in msg or "employees" in msg:
                    if role in ["HR", "ADMIN"]:
                        employee_count = Employee.objects.filter(deleted_at__isnull=True).count()
                        return Response({"status": True, "records": {"reply": f"There are {employee_count} employees."}}, status=200)
                    return Response({"status": True, "records": {"reply": "You can view employee counts if you have HR or Admin access."}}, status=200)
                if role in ["HR", "ADMIN"] and "leave" in msg:
                    pending = LeaveRequest.objects.filter(status="PENDING", deleted_at__isnull=True).count()
                    return Response({"status": True, "records": {"reply": f"There are {pending} pending leave request(s)."}}, status=200)
                if "project" in msg:
                    total_projects = Project.objects.filter(deleted_at__isnull=True).count()
                    return Response({"status": True, "records": {"reply": f"There are {total_projects} project(s)."}}, status=200)
                if "task" in msg:
                    if role in ["USER", "EMPLOYEE"]:
                        total_tasks = Task.objects.filter(assigned_to=user, deleted_at__isnull=True).count()
                        return Response({"status": True, "records": {"reply": f"You have {total_tasks} assigned task(s)."}}, status=200)
                    total_tasks = Task.objects.filter(deleted_at__isnull=True).count()
                    return Response({"status": True, "records": {"reply": f"There are {total_tasks} task(s) in the system."}}, status=200)

            # HR/ADMIN: upcoming birthdays (next 30 days)
            if role in ["HR", "ADMIN"] and ("birthday" in msg or "birthdays" in msg):
                today = timezone.now().date()
                upcoming = []
                for emp in Employee.objects.filter(deleted_at__isnull=True).select_related("user"):
                    dob = emp.user.date_of_birth if emp.user else None
                    if not dob:
                        continue
                    this_year = timezone.datetime(today.year, dob.month, dob.day).date()
                    if this_year < today:
                        this_year = timezone.datetime(today.year + 1, dob.month, dob.day).date()
                    delta = (this_year - today).days
                    if 0 <= delta <= 30:
                        upcoming.append((this_year, emp.user.name))
                upcoming.sort(key=lambda x: x[0])
                if upcoming:
                    names = [f"{n} ({d.strftime('%b %d')})" for d, n in upcoming[:10]]
                    return Response({"status": True, "records": {"reply": "Upcoming birthdays: " + ", ".join(names)}}, status=200)
                return Response({"status": True, "records": {"reply": "No upcoming birthdays in the next 30 days."}}, status=200)

            # HR/ADMIN: employee salary lookup
            if role in ["HR", "ADMIN"] and ("salary" in msg or "pay" in msg):
                match = _match_employee_from_message(msg)
                if not match:
                    return Response({"status": True, "records": {"reply": "Please specify the employee full name to fetch salary."}}, status=200)
                salary = match.salary or "Not set"
                return Response({"status": True, "records": {"reply": f"{match.user.name}'s salary is {salary}."}}, status=200)

            # HR/ADMIN: employee details by name
            if role in ["HR", "ADMIN"] and ("details" in msg or "profile" in msg or "about" in msg):
                match = _match_employee_from_message(msg)
                if not match:
                    return Response({"status": True, "records": {"reply": "Please specify the employee full name to fetch details."}}, status=200)
                dept = match.department.name if match.department else "Not set"
                doj = match.date_of_joining or "Not set"
                phone = match.phone or "Not set"
                designation = match.designation or "Not set"
                email = match.user.email if match.user else "Not set"
                reply = (
                    f"Employee: {match.user.name}. "
                    f"Email: {email}. "
                    f"Designation: {designation}. "
                    f"Department: {dept}. "
                    f"Date of joining: {doj}. "
                    f"Phone: {phone}."
                )
                return Response({"status": True, "records": {"reply": reply}}, status=200)

            # HR/ADMIN: last payroll date
            if role in ["HR", "ADMIN"] and ("last payroll" in msg or "last payrun" in msg):
                last_payrun = PayRun.objects.filter(finalized_at__isnull=False).order_by("-finalized_at").first()
                if last_payrun:
                    return Response({"status": True, "records": {"reply": f"Last payroll finalized on {last_payrun.finalized_at.date()}."}}, status=200)
                last_period = PayrollPeriod.objects.filter(status__in=["Paid", "Approved"]).order_by("-end_date").first()
                if last_period:
                    return Response({"status": True, "records": {"reply": f"Last payroll period ended on {last_period.end_date}."}}, status=200)
                return Response({"status": True, "records": {"reply": "No payroll has been finalized yet."}}, status=200)

            # HR/ADMIN: late employees (no attendance today)
            if role in ["HR", "ADMIN"] and ("late employees" in msg or "not checked in" in msg or "absent today" in msg):
                today = timezone.now().date()
                attended_ids = Attendance.objects.filter(date=today).values_list("employee_id", flat=True)
                late_emps = Employee.objects.filter(deleted_at__isnull=True).exclude(id__in=attended_ids)[:10]
                names = [e.user.name for e in late_emps if e.user]
                if names:
                    return Response({"status": True, "records": {"reply": f"Employees not checked in today: {', '.join(names)}."}}, status=200)
                return Response({"status": True, "records": {"reply": "All employees have checked in today (or no attendance data available)."}}, status=200)

            # HR/ADMIN: approve leave by ID
            if role in ["HR", "ADMIN"] and "approve leave" in msg:
                leave_id_match = re.search(r"[0-9a-fA-F-]{32,36}", msg)
                if not leave_id_match:
                    return Response({"status": True, "records": {"reply": "Please provide the leave request ID to approve."}}, status=200)
                leave_id = leave_id_match.group(0)
                leave = LeaveRequest.objects.filter(id=leave_id, deleted_at__isnull=True).first()
                if not leave:
                    return Response({"status": True, "records": {"reply": "Leave request not found."}}, status=200)
                leave.status = "APPROVED"
                leave.approved_by = user
                leave.approved_at = timezone.now()
                leave.save(update_fields=["status", "approved_by", "approved_at"])
                return Response({"status": True, "records": {"reply": f"Approved leave request {leave_id}."}}, status=200)

            # USER/EMPLOYEE: request leave action
            if role in ["USER", "EMPLOYEE"] and ("request leave" in msg or "apply leave" in msg):
                dates = re.findall(r"\d{4}-\d{2}-\d{2}", msg)
                if len(dates) < 2:
                    return Response({"status": True, "records": {"reply": "Please provide start and end dates in YYYY-MM-DD format."}}, status=200)
                employee = Employee.objects.filter(user=user, deleted_at__isnull=True).first()
                if not employee:
                    return Response({"status": True, "records": {"reply": "Employee profile not found."}}, status=200)
                LeaveRequest.objects.create(
                    employee=employee,
                    start_date=dates[0],
                    end_date=dates[1],
                    reason="Requested via AI helper",
                    status="PENDING"
                )
                return Response({"status": True, "records": {"reply": f"Leave request submitted for {dates[0]} to {dates[1]}."}}, status=200)

            # MANAGER/ADMIN: create task action
            if role in ["MANAGER", "ADMIN"] and "create task" in msg:
                title_match = re.search(r"create task[: ]+(.*)", msg)
                title = title_match.group(1).strip().capitalize() if title_match else ""
                if not title:
                    return Response({"status": True, "records": {"reply": "Please provide a task title. Example: create task Review API spec."}}, status=200)

                project = None
                if role == "MANAGER":
                    employee = Employee.objects.filter(user=user, deleted_at__isnull=True).first()
                    if employee:
                        project_ids = list(ManagerMapping.objects.filter(manager=employee, deleted_at__isnull=True).values_list("project_id", flat=True))
                        project = Project.objects.filter(id__in=project_ids, deleted_at__isnull=True).first()
                else:
                    project = Project.objects.filter(deleted_at__isnull=True).first()

                if not project:
                    return Response({"status": True, "records": {"reply": "No project found to attach this task. Please specify a project."}}, status=200)

                task = Task.objects.create(
                    project=project,
                    title=title,
                    status="TODO",
                    priority="MEDIUM"
                )
                return Response({"status": True, "records": {"reply": f"Created task '{task.title}' in project {project.name}."}}, status=200)

            if not is_ollama_running():
                return Response({"status": True, "records": {"reply": "Ollama is offline. Please start the Ollama service to use the AI helper."}}, status=200)

            context_key = f"global_ai_context:{user.id}:{role}"
            context = cache.get(context_key)
            if not context:
                context = build_role_context(user, role)
                cache.set(context_key, context, timeout=300)

            role_prompt = role_system_prompt(role)

            history_lines = []
            for h in history[-8:]:
                r = h.get("role", "user")
                t = h.get("text", "")
                history_lines.append(f"{r.upper()}: {t}")

            prompt = f"""
{role_prompt}

CONTEXT:
{context}

CHAT HISTORY:
{chr(10).join(history_lines)}

USER QUESTION:
{message}
"""

            try:
                reply = ollama_generate(prompt, timeout=10)
            except Timeout:
                return Response({
                    "status": True,
                    "records": {"reply": "AI helper timed out. Try a narrower question or ask for a specific count."}
                }, status=200)

            final_reply = reply.strip() or "No response"
            cache.set(cache_key, final_reply, timeout=1800)
            return Response({"status": True, "records": {"reply": final_reply}}, status=200)

        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=400)


def role_system_prompt(role: str) -> str:
    prompts = {
        "ADMIN": "You are an executive operations assistant. Tone: crisp, executive summary. Provide concise, high-level answers using system data only.",
        "HR": "You are an HR operations assistant. Tone: supportive and compliance-aware. Focus on employee, leave, and compliance data. Do not expose data outside HR scope.",
        "MANAGER": "You are a project manager assistant. Tone: tactical and delivery-focused. Focus on managed projects, sprints, and team tasks only.",
        "USER": "You are a personal work assistant. Tone: concise and helpful. Focus only on the user's tasks, leaves, and assignments.",
        "EMPLOYEE": "You are a personal work assistant. Tone: concise and helpful. Focus only on the user's tasks, leaves, and assignments.",
    }
    return prompts.get(role, prompts["USER"])


def build_role_context(user: User, role: str) -> str:
    if role in ["HR", "ADMIN"]:
        employee_count = Employee.objects.filter(deleted_at__isnull=True).count()
        pending_leaves = LeaveRequest.objects.filter(status="PENDING", deleted_at__isnull=True)[:5]
        pending_lines = [f"- {lr.employee.user.name} ({lr.start_date} to {lr.end_date})" for lr in pending_leaves]
        today = timezone.now().date()
        attended_ids = Attendance.objects.filter(date=today).values_list("employee_id", flat=True)
        late_emps = Employee.objects.filter(deleted_at__isnull=True).exclude(id__in=attended_ids)[:5]
        late_lines = [f"- {e.user.name}" for e in late_emps if e.user]
        return f"""
Employees: {employee_count}
Pending leave requests:
{chr(10).join(pending_lines) if pending_lines else 'None'}
Not checked in today:
{chr(10).join(late_lines) if late_lines else 'None'}
"""

    if role == "MANAGER":
        employee = Employee.objects.filter(user=user, deleted_at__isnull=True).first()
        if not employee:
            return "No manager profile found."
        project_ids = list(ManagerMapping.objects.filter(manager=employee, deleted_at__isnull=True).values_list("project_id", flat=True))
        projects = Project.objects.filter(id__in=project_ids, deleted_at__isnull=True)
        sprints = Sprint.objects.filter(project_id__in=project_ids, deleted_at__isnull=True)[:5]
        tasks = Task.objects.filter(project_id__in=project_ids, deleted_at__isnull=True)[:15]
        project_lines = [f"- {p.name} ({p.status})" for p in projects[:5]]
        sprint_lines = [f"- {s.name} ({s.status})" for s in sprints]
        task_lines = [f"- {t.title} | {t.status} | {t.priority}" for t in tasks]
        return f"""
Managed projects:
{chr(10).join(project_lines) if project_lines else 'None'}
Active sprints:
{chr(10).join(sprint_lines) if sprint_lines else 'None'}
Tasks (sample):
{chr(10).join(task_lines) if task_lines else 'None'}
"""

    # USER / EMPLOYEE
    tasks = Task.objects.filter(assigned_to=user, deleted_at__isnull=True)[:15]
    task_lines = [f"- {t.title} | {t.status} | {t.priority}" for t in tasks]
    employee = Employee.objects.filter(user=user, deleted_at__isnull=True).first()
    balance = None
    if employee:
        bal = LeaveBalance.objects.filter(employee=employee).first()
        balance = bal.balance if bal else None
    return f"""
Assigned tasks (sample):
{chr(10).join(task_lines) if task_lines else 'None'}
Leave balance: {balance if balance is not None else 'N/A'}
"""
