from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from django.contrib.auth.models import Group

from authentication.models.user import User
from company.models.company_model import Company, UserMapping as CompanyUserMapping
from department.models.department_model import Department
from hr_management.models.hr_management_models import Employee, LeaveBalance, LeaveRequest, Attendance
from payroll.models.payroll_models import PayrollPeriod, PayRun, Payroll
from payroll.models.benefits_models import BenefitPlan, BenefitEnrollment
from payroll.models.expense_models import ExpenseCategory, ExpenseClaim
from payroll.models.loan_models import LoanAdvance
from projects.models.project_model import Project, ManagerMapping, UserMapping as ProjectUserMapping
from projects.models.project_member_model import ProjectMember
from projects.models.sprint_model import Sprint
from projects.models.task_model import Task
from time_tracking.models.time_tracking_models import TimeEntry


class Command(BaseCommand):
    help = "Truncate database and create deterministic demo org data for 2 companies"

    PASSWORD = "Pass@123"

    def add_arguments(self, parser):
        parser.add_argument("--truncate", action="store_true", help="Flush DB before seeding")

    def handle(self, *args, **options):
        if options.get("truncate"):
            self.stdout.write("Clearing existing data...")
            self._clear_data()
            self.stdout.write(self.style.SUCCESS("Existing data cleared."))

        self.stdout.write("Seeding demo dataset...")
        departments = self._create_departments()
        orgs = self._create_companies_and_people(departments)
        self._create_projects_and_sprints(orgs)
        self._create_payroll(orgs)
        self._create_benefits_expenses_loans(orgs)
        self._create_leave_attendance_time(orgs)

        self.stdout.write(self.style.SUCCESS("Demo dataset created successfully."))
        self.stdout.write(self.style.SUCCESS("Password for all seeded users: Pass@123"))
        self.stdout.write("---- LOGIN USERS ----")
        for row in self._login_rows(orgs):
            self.stdout.write(row)

    def _clear_data(self):
        # Cleanup orphan legacy tables (if present) from removed apps
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF to_regclass('public.teams_teammembersmapping') IS NOT NULL THEN
                        EXECUTE 'TRUNCATE TABLE public.teams_teammembersmapping RESTART IDENTITY CASCADE';
                    END IF;
                    IF to_regclass('public.teams_team') IS NOT NULL THEN
                        EXECUTE 'TRUNCATE TABLE public.teams_team RESTART IDENTITY CASCADE';
                    END IF;
                END $$;
                """
            )

        models_in_delete_order = [
            TimeEntry,
            Attendance,
            LeaveRequest,
            LeaveBalance,
            Task,
            Sprint,
            ProjectMember,
            ProjectUserMapping,
            ManagerMapping,
            Project,
            Payroll,
            PayRun,
            PayrollPeriod,
            LoanAdvance,
            ExpenseClaim,
            ExpenseCategory,
            BenefitEnrollment,
            BenefitPlan,
            Employee,
            CompanyUserMapping,
            User,
            Company,
            Department,
            Group,
        ]
        for model in models_in_delete_order:
            model.objects.all().delete()

    def _create_departments(self):
        names = [
            ("Human Resources", "HR operations"),
            ("Engineering", "Engineering department"),
            ("Product Management", "Product department"),
            ("Sales", "Sales department"),
            ("Quality Assurance", "QA department"),
        ]
        departments = {}
        for name, desc in names:
            dept, _ = Department.objects.get_or_create(name=name, defaults={"description": desc})
            departments[name] = dept
        return departments

    def _create_companies_and_people(self, departments):
        companies = [
            {"name": "Digital Dynamics", "pan": "AAACD1111A", "tan": "BLRD11111B"},
            {"name": "TechNova Solutions", "pan": "AAACT2222B", "tan": "BLRT22222C"},
        ]
        orgs = []
        for c_idx, c in enumerate(companies, start=1):
            company = Company.objects.create(
                name=c["name"],
                pan=c["pan"],
                tan=c["tan"],
                description=f"{c['name']} seeded demo company",
            )

            hr_user = self._create_user(
                username=f"hr_c{c_idx}",
                name=f"HR Lead C{c_idx}",
                email=f"hr_c{c_idx}@demo.local",
                role="HR",
            )
            hr_emp = self._create_employee(
                user=hr_user,
                company=company,
                department=departments["Human Resources"],
                designation="HR Manager",
                salary=90000,
            )

            managers = []
            for m_idx in range(1, 4):
                m_user = self._create_user(
                    username=f"mgr_c{c_idx}_{m_idx}",
                    name=f"Manager C{c_idx}-{m_idx}",
                    email=f"mgr_c{c_idx}_{m_idx}@demo.local",
                    role="MANAGER",
                )
                m_emp = self._create_employee(
                    user=m_user,
                    company=company,
                    department=departments["Engineering"] if m_idx % 2 else departments["Product Management"],
                    designation="Project Manager",
                    salary=120000 + (m_idx * 5000),
                )

                team_members = []
                for t_idx in range(1, 6):
                    u = self._create_user(
                        username=f"mem_c{c_idx}_{m_idx}_{t_idx}",
                        name=f"Member C{c_idx}-{m_idx}-{t_idx}",
                        email=f"mem_c{c_idx}_{m_idx}_{t_idx}@demo.local",
                        role="USER",
                    )
                    e = self._create_employee(
                        user=u,
                        company=company,
                        department=departments["Engineering"] if t_idx % 2 else departments["Quality Assurance"],
                        designation="Software Engineer" if t_idx % 2 else "QA Engineer",
                        salary=50000 + t_idx * 3500,
                    )
                    team_members.append({"user": u, "employee": e})

                managers.append({"user": m_user, "employee": m_emp, "team": team_members})

            orgs.append({"company": company, "hr": {"user": hr_user, "employee": hr_emp}, "managers": managers})
        return orgs

    def _create_projects_and_sprints(self, orgs):
        for org in orgs:
            hr_user = org["hr"]["user"]
            for m_idx, mgr in enumerate(org["managers"], start=1):
                manager_employee = mgr["employee"]
                manager_user = mgr["user"]
                team = mgr["team"]

                for p_idx in range(1, 4):
                    project = Project.objects.create(
                        name=f"{org['company'].name} - M{m_idx} Project {p_idx}",
                        description=f"Seeded project for manager {manager_user.name}",
                        manager=manager_employee,
                        status="Ongoing" if p_idx == 1 else "Planning",
                        start_date=date.today() - timedelta(days=20),
                        end_date=date.today() + timedelta(days=90),
                        priority="HIGH" if p_idx == 1 else "MEDIUM",
                        ai_health_score=65 if p_idx == 1 else 78,
                        updated_by=hr_user,
                    )

                    ManagerMapping.objects.create(manager=manager_employee, project=project)
                    ProjectMember.objects.create(project=project, user=manager_user, role="MANAGER")
                    ProjectUserMapping.objects.create(employee=manager_employee, project=project)
                    ProjectMember.objects.create(project=project, user=hr_user, role="OWNER")

                    for member in team:
                        ProjectMember.objects.get_or_create(
                            project=project, user=member["user"], defaults={"role": "MEMBER"}
                        )
                        ProjectUserMapping.objects.get_or_create(
                            employee=member["employee"], project=project
                        )

                    if p_idx == 1:
                        sprint = Sprint.objects.create(
                            name=f"Sprint A - M{m_idx}",
                            description="Running sprint",
                            project=project,
                            status="ACTIVE",
                            start_date=date.today() - timedelta(days=5),
                            end_date=date.today() + timedelta(days=9),
                            goal="Deliver core features for release",
                            velocity=32,
                            ai_completion_probability=74,
                        )
                        self._create_sprint_tasks(project, sprint, manager_user, team)

    def _create_sprint_tasks(self, project, sprint, manager_user, team):
        statuses = ["TODO", "IN_PROGRESS", "IN_REVIEW", "BLOCKED", "DONE", "TODO", "IN_PROGRESS", "DONE"]
        for idx, st in enumerate(statuses, start=1):
            assigned = team[(idx - 1) % len(team)]["user"]
            Task.objects.create(
                title=f"{project.name} Task {idx}",
                description=f"Seeded task {idx} for {project.name}",
                status=st,
                priority="HIGH" if idx <= 3 else "MEDIUM",
                task_type="TASK",
                project=project,
                sprint=sprint,
                assigned_to=assigned if st != "BLOCKED" else manager_user,
                order=idx - 1,
                story_points=3 if idx % 2 else 5,
                progress_percentage=100 if st == "DONE" else (50 if st == "IN_PROGRESS" else 0),
            )

    def _create_payroll(self, orgs):
        today = date.today()
        cur_start = today.replace(day=1)
        prev_month_end = cur_start - timedelta(days=1)
        prev_start = prev_month_end.replace(day=1)

        current_period = PayrollPeriod.objects.create(
            start_date=cur_start,
            end_date=today,
            period_name=today.strftime("%B %Y"),
            financial_year=f"{today.year}-{today.year + 1}",
            status="Processing",
        )
        prev_period = PayrollPeriod.objects.create(
            start_date=prev_start,
            end_date=prev_month_end,
            period_name=prev_month_end.strftime("%B %Y"),
            financial_year=f"{prev_month_end.year}-{prev_month_end.year + 1}",
            status="Paid",
        )

        any_hr_user = orgs[0]["hr"]["user"]
        current_run = PayRun.objects.create(payroll_period=current_period, created_by=any_hr_user, status="IN_PROGRESS")
        prev_run = PayRun.objects.create(payroll_period=prev_period, created_by=any_hr_user, status="FINALIZED")

        all_employees = Employee.objects.filter(deleted_at__isnull=True).select_related("user")
        for emp in all_employees:
            base_salary = Decimal(str(emp.salary or "50000"))
            self._create_single_payroll(emp, current_period, current_run, base_salary, "CALCULATED")
            self._create_single_payroll(emp, prev_period, prev_run, base_salary, "APPROVED")

        self._refresh_run_totals(current_run)
        self._refresh_run_totals(prev_run)

    def _create_single_payroll(self, emp, period, pay_run, base_salary, status_value):
        basic = (base_salary * Decimal("0.50")).quantize(Decimal("0.01"))
        hra = (base_salary * Decimal("0.20")).quantize(Decimal("0.01"))
        transport = (base_salary * Decimal("0.10")).quantize(Decimal("0.01"))
        other = (base_salary * Decimal("0.20")).quantize(Decimal("0.01"))
        gross = basic + hra + transport + other
        pf = (basic * Decimal("0.12")).quantize(Decimal("0.01"))
        pt = Decimal("200.00")
        it = (gross * Decimal("0.08")).quantize(Decimal("0.01"))
        ded = pf + pt + it
        net = gross - ded

        Payroll.objects.create(
            employee=emp,
            pay_run=pay_run,
            payroll_period=period,
            basic_salary=basic,
            house_rent_allowance=hra,
            transport_allowance=transport,
            other_allowances=other,
            provident_fund=pf,
            professional_tax=pt,
            income_tax=it,
            gross_salary=gross,
            total_deductions=ded,
            net_salary=net,
            overtime_hours=Decimal("2.0"),
            overtime_rate=Decimal("300.00"),
            overtime_amount=Decimal("600.00"),
            working_days=22,
            present_days=21,
            paid_leave_days=1,
            payable_days=22,
            lop_days=0,
            status=status_value,
        )

    def _refresh_run_totals(self, pay_run):
        qs = Payroll.objects.filter(pay_run=pay_run, deleted_at__isnull=True)
        pay_run.total_employees = qs.count()
        pay_run.total_gross_salary = qs.aggregate(v=SumSafe("gross_salary"))["v"]
        pay_run.total_deductions = qs.aggregate(v=SumSafe("total_deductions"))["v"]
        pay_run.total_net_salary = qs.aggregate(v=SumSafe("net_salary"))["v"]
        pay_run.save(update_fields=["total_employees", "total_gross_salary", "total_deductions", "total_net_salary"])

    def _create_benefits_expenses_loans(self, orgs):
        plan = BenefitPlan.objects.create(
            name="Basic Health Cover",
            description="Demo seeded health plan",
            plan_type="Health Insurance",
            provider="Demo Provider",
            coverage_amount=Decimal("500000.00"),
            employee_contribution=Decimal("1200.00"),
            employer_contribution=Decimal("2400.00"),
            is_mandatory=False,
            waiting_period_days=0,
            enrollment_start_date=date.today() - timedelta(days=10),
            enrollment_end_date=date.today() + timedelta(days=30),
            plan_year_start=date.today().replace(month=1, day=1),
            plan_year_end=date.today().replace(month=12, day=31),
            is_active=True,
        )

        categories = [
            ExpenseCategory.objects.create(name="Travel", description="Travel expenses", max_amount_per_claim=10000),
            ExpenseCategory.objects.create(name="Software & Licenses", description="Software costs", max_amount_per_claim=25000),
        ]

        for org in orgs:
            hr_user = org["hr"]["user"]
            for mgr in org["managers"]:
                # one enrolled member per manager team (for realistic dashboards)
                enrolled_emp = mgr["team"][0]["employee"]
                BenefitEnrollment.objects.create(
                    employee=enrolled_emp,
                    benefit_plan=plan,
                    effective_date=date.today(),
                    coverage_level="Employee Only",
                    employee_monthly_cost=Decimal("1200.00"),
                    employer_monthly_cost=Decimal("2400.00"),
                    status="Active",
                    submitted_by=hr_user,
                    approved_by=hr_user,
                    approved_at=timezone.now(),
                )

                for i, member in enumerate(mgr["team"][:2], start=1):
                    ExpenseClaim.objects.create(
                        employee=member["employee"],
                        category=categories[i % len(categories)],
                        title=f"Demo expense {i}",
                        description="Seeded expense claim",
                        amount=Decimal("2500.00") + Decimal(i * 400),
                        expense_date=date.today() - timedelta(days=3 * i),
                        status="Submitted" if i == 1 else "Approved",
                        submitted_at=timezone.now() - timedelta(days=i),
                        reviewed_by=hr_user if i != 1 else None,
                        reviewed_at=timezone.now() - timedelta(days=max(i - 1, 0)) if i != 1 else None,
                        reimbursement_amount=Decimal("2000.00") if i != 1 else None,
                    )

                LoanAdvance.objects.create(
                    employee=mgr["team"][0]["employee"],
                    loan_type="Loan",
                    principal_amount=Decimal("250000.00"),
                    emi_amount=Decimal("5000.00"),
                    outstanding_balance=Decimal("220000.00"),
                    tenure_months=48,
                    disbursed_date=date.today() - timedelta(days=90),
                    next_deduction_date=date.today() + timedelta(days=20),
                    status="Active",
                    notes="Seeded home loan",
                )

    def _create_leave_attendance_time(self, orgs):
        today = timezone.localdate()
        for org in orgs:
            all_emp = [org["hr"]["employee"]]
            for mgr in org["managers"]:
                all_emp.append(mgr["employee"])
                all_emp.extend([m["employee"] for m in mgr["team"]])

            for e in all_emp:
                LeaveBalance.objects.get_or_create(employee=e, defaults={"balance": 24})

                for d in range(0, 5):
                    day = today - timedelta(days=d)
                    in_dt = timezone.make_aware(datetime.combine(day, datetime.min.time().replace(hour=9, minute=30)))
                    out_dt = timezone.make_aware(datetime.combine(day, datetime.min.time().replace(hour=18, minute=15)))
                    TimeEntry.objects.update_or_create(
                        user=e.user,
                        date=day,
                        defaults={
                            "login_time": in_dt,
                            "logout_time": out_dt,
                            "description": "Seeded time entry",
                        },
                    )
                    Attendance.objects.update_or_create(
                        employee=e,
                        date=day,
                        defaults={"in_time": in_dt.time(), "out_time": out_dt.time()},
                    )

            # a few pending leaves for dashboard cards
            for mgr in org["managers"]:
                member = mgr["team"][1]["employee"]
                LeaveRequest.objects.create(
                    employee=member,
                    leave_type="CASUAL",
                    start_date=today + timedelta(days=2),
                    end_date=today + timedelta(days=3),
                    reason="Personal work",
                    status="PENDING",
                )

    def _create_user(self, username, name, email, role):
        user = User.objects.create_user(
            username=username,
            email=email,
            name=name,
            password=self.PASSWORD,
            role=role,
            date_of_birth=date(1994, 1, 15),
        )
        return user

    def _create_employee(self, user, company, department, designation, salary):
        emp = Employee.objects.create(
            user=user,
            company=company,
            department=department,
            salary=str(salary),
            date_of_joining=date.today() - timedelta(days=400),
            designation=designation,
            phone="9999999999",
            tax_regime="NEW",
        )
        CompanyUserMapping.objects.get_or_create(user=user, company=company)
        return emp

    def _login_rows(self, orgs):
        rows = []
        for c_idx, org in enumerate(orgs, start=1):
            rows.append(f"[Company {c_idx}] HR -> username: hr_c{c_idx} | password: {self.PASSWORD}")
            for m_idx, _mgr in enumerate(org["managers"], start=1):
                rows.append(
                    f"[Company {c_idx}] Manager {m_idx} -> username: mgr_c{c_idx}_{m_idx} | password: {self.PASSWORD}"
                )
                rows.append(
                    f"[Company {c_idx}] Team {m_idx} sample member -> username: mem_c{c_idx}_{m_idx}_1 | password: {self.PASSWORD}"
                )
        return rows


def SumSafe(field_name):
    from django.db.models import Sum

    return Sum(field_name, default=Decimal("0.00"))
