# management/commands/seed_payroll.py

from django.core.management.base import BaseCommand
from django.db import transaction
import random
from datetime import date, timedelta, datetime
from faker import Faker
from decimal import Decimal

# Import payroll models
from payroll.models.benefits_models import BenefitPlan, BenefitEnrollment, TaxConfiguration
from payroll.models.expense_models import ExpenseCategory, ExpenseClaim, ExpenseApprovalWorkflow
from payroll.models.payroll_models import PayrollPeriod, Payroll, PerformanceMetric

# Import related models
from hr_management.models.hr_management_models import Employee
from authentication.models.user import User

fake = Faker()

class Command(BaseCommand):
    help = 'Seed database with comprehensive payroll fake data'

    def add_arguments(self, parser):
        parser.add_argument('--benefit-plans', type=int, default=8, help='Number of benefit plans')
        parser.add_argument('--expense-categories', type=int, default=12, help='Number of expense categories')
        parser.add_argument('--payroll-periods', type=int, default=6, help='Number of payroll periods')
        parser.add_argument('--clear', action='store_true', help='Clear existing payroll data')

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_payroll_data()

        with transaction.atomic():
            # Get existing employees and users
            employees = list(Employee.objects.all())
            users = list(User.objects.all())
            
            if not employees:
                self.stdout.write(self.style.ERROR('❌ No employees found. Please run seed_all.py first.'))
                return

            # Seed payroll data
            tax_configs = self.seed_tax_configurations()
            benefit_plans = self.seed_benefit_plans(options['benefit_plans'])
            self.seed_benefit_enrollments(employees, benefit_plans, users)
            expense_categories = self.seed_expense_categories(options['expense_categories'])
            self.seed_expense_claims(employees, expense_categories, users)
            payroll_periods = self.seed_payroll_periods(options['payroll_periods'])
            self.seed_payrolls(employees, payroll_periods, users)
            self.seed_performance_metrics(employees, payroll_periods)

            self.stdout.write(self.style.SUCCESS('✅ Payroll database seeding completed successfully!'))

    def clear_payroll_data(self):
        """Clear existing payroll data in correct order"""
        self.stdout.write('🗑️ Clearing existing payroll data...')
        
        # Clear in order to avoid FK constraint issues
        ExpenseApprovalWorkflow.objects.all().delete()
        ExpenseClaim.objects.all().delete()
        ExpenseCategory.objects.all().delete()
        
        PerformanceMetric.objects.all().delete()
        Payroll.objects.all().delete()
        PayrollPeriod.objects.all().delete()
        
        BenefitEnrollment.objects.all().delete()
        BenefitPlan.objects.all().delete()
        TaxConfiguration.objects.all().delete()
        
        self.stdout.write('✅ Payroll data cleared successfully!')

    def seed_tax_configurations(self):
        """Seed tax configurations for different regions"""
        self.stdout.write('💰 Creating tax configurations...')
        
        tax_configs = []
        
        # Indian tax configuration - FIXED: Use None instead of float('inf')
        indian_tax_slabs = [
            {"min": 0, "max": 250000, "rate": 0},
            {"min": 250001, "max": 500000, "rate": 5},
            {"min": 500001, "max": 1000000, "rate": 20},
            {"min": 1000001, "max": None, "rate": 30}  # Use None instead of float('inf')
        ]
        
        indian_config = TaxConfiguration.objects.create(
            country='India',
            state='Karnataka',
            tax_year='2024-25',
            tax_slabs=indian_tax_slabs,
            standard_deduction=Decimal('50000'),
            professional_tax_rate=Decimal('2.5'),
            provident_fund_rate=Decimal('12.0'),
            cess_rate=Decimal('4.0'),
            surcharge_threshold=Decimal('5000000'),
            surcharge_rate=Decimal('10.0'),
            is_active=True
        )
        tax_configs.append(indian_config)
        
        # US tax configuration - FIXED: Use None instead of float('inf')
        us_tax_slabs = [
            {"min": 0, "max": 10275, "rate": 10},
            {"min": 10276, "max": 41775, "rate": 12},
            {"min": 41776, "max": 89450, "rate": 22},
            {"min": 89451, "max": 190750, "rate": 24},
            {"min": 190751, "max": None, "rate": 32}  # Use None instead of float('inf')
        ]
        
        us_config = TaxConfiguration.objects.create(
            country='United States',
            state='California',
            tax_year='2024',
            tax_slabs=us_tax_slabs,
            standard_deduction=Decimal('12950'),
            professional_tax_rate=Decimal('0'),
            provident_fund_rate=Decimal('6.2'),
            cess_rate=Decimal('0'),
            surcharge_threshold=Decimal('1000000'),
            surcharge_rate=Decimal('3.8'),
            is_active=True
        )
        tax_configs.append(us_config)
        
        self.stdout.write(f'✅ Created {len(tax_configs)} tax configurations')
        return tax_configs

    def seed_benefit_plans(self, num_plans):
        """Seed benefit plans with realistic data"""
        self.stdout.write(f'🏥 Creating {num_plans} benefit plans...')
        
        benefit_plans = []
        
        # Predefined benefit plan templates
        plan_templates = [
            {
                'name': 'Comprehensive Health Insurance',
                'plan_type': 'Health Insurance',
                'provider': 'HealthCorp Insurance',
                'coverage_amount': Decimal('500000'),
                'employee_contribution': Decimal('2000'),
                'employer_contribution': Decimal('8000'),
                'is_mandatory': True,
                'eligibility_criteria': 'All full-time employees',
                'waiting_period_days': 30
            },
            {
                'name': 'Basic Life Insurance',
                'plan_type': 'Life Insurance',
                'provider': 'LifeSecure Insurance',
                'coverage_amount': Decimal('1000000'),
                'employee_contribution': Decimal('500'),
                'employer_contribution': Decimal('1500'),
                'is_mandatory': True,
                'eligibility_criteria': 'All employees',
                'waiting_period_days': 0
            },
            {
                'name': 'Dental Care Plan',
                'plan_type': 'Dental',
                'provider': 'SmileCare Dental',
                'coverage_amount': Decimal('50000'),
                'employee_contribution': Decimal('800'),
                'employer_contribution': Decimal('1200'),
                'is_mandatory': False,
                'eligibility_criteria': 'All employees after 90 days',
                'waiting_period_days': 90
            },
            {
                'name': 'Vision Care Plan',
                'plan_type': 'Vision',
                'provider': 'ClearSight Vision',
                'coverage_amount': Decimal('25000'),
                'employee_contribution': Decimal('300'),
                'employer_contribution': Decimal('700'),
                'is_mandatory': False,
                'eligibility_criteria': 'All employees',
                'waiting_period_days': 30
            },
            {
                'name': 'Employee Provident Fund',
                'plan_type': 'Retirement',
                'provider': 'EPFO',
                'coverage_amount': None,
                'employee_contribution': Decimal('1800'),
                'employer_contribution': Decimal('1800'),
                'is_mandatory': True,
                'eligibility_criteria': 'All employees with salary > 15000',
                'waiting_period_days': 0
            },
            {
                'name': 'Flexible Spending Account',
                'plan_type': 'Flexible Spending',
                'provider': 'FlexBenefits Corp',
                'coverage_amount': Decimal('100000'),
                'employee_contribution': Decimal('2000'),
                'employer_contribution': Decimal('0'),
                'is_mandatory': False,
                'eligibility_criteria': 'All full-time employees',
                'waiting_period_days': 30
            },
            {
                'name': 'Transportation Allowance',
                'plan_type': 'Transportation',
                'provider': 'Company Transportation',
                'coverage_amount': Decimal('3000'),
                'employee_contribution': Decimal('0'),
                'employer_contribution': Decimal('3000'),
                'is_mandatory': False,
                'eligibility_criteria': 'All employees',
                'waiting_period_days': 0
            },
            {
                'name': 'Meal Vouchers',
                'plan_type': 'Other',
                'provider': 'FoodCorp Vouchers',
                'coverage_amount': Decimal('2200'),
                'employee_contribution': Decimal('0'),
                'employer_contribution': Decimal('2200'),
                'is_mandatory': False,
                'eligibility_criteria': 'All office employees',
                'waiting_period_days': 0
            }
        ]
        
        # Create benefit plans
        for i in range(min(num_plans, len(plan_templates))):
            template = plan_templates[i]
            
            # Generate enrollment dates
            enrollment_start = fake.date_between(start_date='-6m', end_date='-3m')
            enrollment_end = enrollment_start + timedelta(days=30)
            plan_year_start = date(date.today().year, 1, 1)
            plan_year_end = date(date.today().year, 12, 31)
            
            benefit_plan = BenefitPlan.objects.create(
                name=template['name'],
                description=fake.text(max_nb_chars=200),
                plan_type=template['plan_type'],
                provider=template['provider'],
                coverage_amount=template['coverage_amount'],
                employee_contribution=template['employee_contribution'],
                employer_contribution=template['employer_contribution'],
                is_mandatory=template['is_mandatory'],
                eligibility_criteria=template['eligibility_criteria'],
                waiting_period_days=template['waiting_period_days'],
                enrollment_start_date=enrollment_start,
                enrollment_end_date=enrollment_end,
                plan_year_start=plan_year_start,
                plan_year_end=plan_year_end,
                is_active=True
            )
            
            benefit_plans.append(benefit_plan)
        
        self.stdout.write(f'✅ Created {len(benefit_plans)} benefit plans')
        return benefit_plans

    def seed_benefit_enrollments(self, employees, benefit_plans, users):
        """Seed benefit enrollments for employees"""
        self.stdout.write('📋 Creating benefit enrollments...')
        
        enrollments_created = 0
        
        for employee in employees:
            # Each employee enrolls in 3-6 benefit plans
            num_enrollments = random.randint(3, min(6, len(benefit_plans)))
            selected_plans = random.sample(benefit_plans, num_enrollments)
            
            for plan in selected_plans:
                # Skip if already enrolled
                if BenefitEnrollment.objects.filter(employee=employee, benefit_plan=plan).exists():
                    continue
                
                enrollment_date = fake.date_between(start_date='-4m', end_date='-1m')
                effective_date = enrollment_date + timedelta(days=plan.waiting_period_days)
                
                # Determine coverage level based on random choice
                coverage_levels = ['Employee Only', 'Employee + Spouse', 'Employee + Children', 'Family']
                coverage_level = random.choice(coverage_levels)
                
                # Set dependent information based on coverage
                spouse_covered = coverage_level in ['Employee + Spouse', 'Family']
                children_count = random.randint(0, 3) if coverage_level in ['Employee + Children', 'Family'] else 0
                
                # Calculate monthly costs (could vary based on coverage level)
                coverage_multiplier = {
                    'Employee Only': 1.0,
                    'Employee + Spouse': 1.8,
                    'Employee + Children': 1.6,
                    'Family': 2.2
                }[coverage_level]
                
                employee_monthly_cost = plan.employee_contribution * Decimal(str(coverage_multiplier))
                employer_monthly_cost = plan.employer_contribution * Decimal(str(coverage_multiplier))
                
                BenefitEnrollment.objects.create(
                    employee=employee,
                    benefit_plan=plan,
                    enrollment_date=enrollment_date,
                    effective_date=effective_date,
                    end_date=None,
                    coverage_level=coverage_level,
                    spouse_covered=spouse_covered,
                    children_count=children_count,
                    employee_monthly_cost=employee_monthly_cost,
                    employer_monthly_cost=employer_monthly_cost,
                    status=random.choice(['Active', 'Active', 'Active', 'Pending']),  # Mostly active
                    submitted_by=employee.user,
                    approved_by=random.choice([u for u in users if u.role in ['HR', 'MANAGER']]) if random.choice([True, False]) else None,
                    approved_at=fake.date_time_between(start_date=enrollment_date, end_date='now') if random.choice([True, False]) else None
                )
                
                enrollments_created += 1
        
        self.stdout.write(f'✅ Created {enrollments_created} benefit enrollments')

    def seed_expense_categories(self, num_categories):
        """Seed expense categories"""
        self.stdout.write(f'🧾 Creating {num_categories} expense categories...')
        
        category_templates = [
            {'name': 'Travel', 'max_amount': 50000, 'requires_receipt': True, 'approval_required': True},
            {'name': 'Meals & Entertainment', 'max_amount': 5000, 'requires_receipt': True, 'approval_required': True},
            {'name': 'Office Supplies', 'max_amount': 10000, 'requires_receipt': True, 'approval_required': False},
            {'name': 'Software & Licenses', 'max_amount': 25000, 'requires_receipt': True, 'approval_required': True},
            {'name': 'Training & Conferences', 'max_amount': 75000, 'requires_receipt': True, 'approval_required': True},
            {'name': 'Communication', 'max_amount': 3000, 'requires_receipt': False, 'approval_required': False},
            {'name': 'Transportation', 'max_amount': 8000, 'requires_receipt': True, 'approval_required': False},
            {'name': 'Accommodation', 'max_amount': 15000, 'requires_receipt': True, 'approval_required': True},
            {'name': 'Medical Expenses', 'max_amount': 20000, 'requires_receipt': True, 'approval_required': True},
            {'name': 'Equipment Purchase', 'max_amount': 100000, 'requires_receipt': True, 'approval_required': True},
            {'name': 'Marketing Materials', 'max_amount': 15000, 'requires_receipt': True, 'approval_required': True},
            {'name': 'Miscellaneous', 'max_amount': 5000, 'requires_receipt': True, 'approval_required': True}
        ]
        
        expense_categories = []
        
        for i in range(min(num_categories, len(category_templates))):
            template = category_templates[i]
            
            category = ExpenseCategory.objects.create(
                name=template['name'],
                description=f"Expenses related to {template['name'].lower()}",
                max_amount_per_claim=Decimal(str(template['max_amount'])),
                requires_receipt=template['requires_receipt'],
                approval_required=template['approval_required']
            )
            
            expense_categories.append(category)
        
        self.stdout.write(f'✅ Created {len(expense_categories)} expense categories')
        return expense_categories

    def seed_expense_claims(self, employees, expense_categories, users):
        """Seed expense claims and approval workflows"""
        self.stdout.write('💳 Creating expense claims...')
        
        claims_created = 0
        
        # Generate expense titles by category
        expense_titles = {
            'Travel': ['Flight tickets to client site', 'Taxi fare to meeting', 'Train tickets for conference'],
            'Meals & Entertainment': ['Client dinner', 'Team lunch', 'Coffee meeting with vendor'],
            'Office Supplies': ['Stationery purchase', 'Printer cartridges', 'Notebooks and pens'],
            'Software & Licenses': ['Adobe Creative Suite license', 'IDE subscription', 'Project management tool'],
            'Training & Conferences': ['Tech conference registration', 'Online course enrollment', 'Workshop attendance'],
            'Communication': ['Mobile phone bill', 'Internet charges', 'Video conference subscription'],
            'Transportation': ['Uber rides', 'Parking fees', 'Bus pass'],
            'Accommodation': ['Hotel stay for business trip', 'Guest house booking', 'Airbnb for conference'],
            'Medical Expenses': ['Health checkup', 'Prescription medicines', 'Medical consultation'],
            'Equipment Purchase': ['Laptop purchase', 'Monitor and accessories', 'Ergonomic chair'],
            'Marketing Materials': ['Brochure printing', 'Banner design', 'Promotional items'],
            'Miscellaneous': ['Emergency expense', 'Unforeseen cost', 'Other business expense']
        }
        
        for employee in random.sample(employees, min(len(employees), 30)):  # 30 employees with expenses
            # Each employee has 2-8 expense claims
            num_claims = random.randint(2, 8)
            
            for _ in range(num_claims):
                category = random.choice(expense_categories)
                
                # Generate realistic amount based on category
                max_amount = float(category.max_amount_per_claim) if category.max_amount_per_claim else 10000
                amount = Decimal(str(random.uniform(100, min(max_amount, 10000))))
                
                # Get appropriate title
                titles = expense_titles.get(category.name, ['Business expense'])
                title = random.choice(titles)
                
                expense_date = fake.date_between(start_date='-90d', end_date='today')
                
                claim = ExpenseClaim.objects.create(
                    employee=employee,
                    category=category,
                    title=title,
                    description=fake.text(max_nb_chars=150),
                    amount=amount,
                    expense_date=expense_date,
                    merchant_name=fake.company(),
                    merchant_category=category.name,
                    status=random.choice(['Submitted', 'Under Review', 'Approved', 'Rejected', 'Paid']),
                    submitted_at=fake.date_time_between(start_date=expense_date, end_date='now'),
                    reviewed_by=random.choice([u for u in users if u.role in ['HR', 'MANAGER']]) if random.choice([True, False]) else None,
                    reviewed_at=fake.date_time_between(start_date=expense_date, end_date='now') if random.choice([True, False]) else None,
                    approval_comments=fake.sentence() if random.choice([True, False]) else '',
                    reimbursement_amount=amount if random.choice([True, False]) else None,
                    paid_at=fake.date_time_between(start_date=expense_date, end_date='now') if random.choice([True, False]) else None,
                    payment_reference=f'REF{random.randint(100000, 999999)}' if random.choice([True, False]) else ''
                )
                
                # Create approval workflow if required
                if category.approval_required and random.choice([True, True, False]):  # 66% chance
                    approvers = [u for u in users if u.role in ['HR', 'MANAGER']]
                    if approvers:
                        ExpenseApprovalWorkflow.objects.create(
                            expense_claim=claim,
                            approver=random.choice(approvers),
                            level=1,
                            status=random.choice(['Pending', 'Approved', 'Rejected']),
                            comments=fake.sentence() if random.choice([True, False]) else '',
                            action_date=fake.date_time_between(start_date=expense_date, end_date='now') if random.choice([True, False]) else None
                        )
                
                claims_created += 1
        
        self.stdout.write(f'✅ Created {claims_created} expense claims')

    def seed_payroll_periods(self, num_periods):
        """Seed payroll periods"""
        self.stdout.write(f'📅 Creating {num_periods} payroll periods...')
        
        payroll_periods = []
        current_date = date.today().replace(day=1)  # Start of current month
        
        for i in range(num_periods):
            # Go back in months
            period_date = current_date - timedelta(days=32 * i)  # Approximate month back
            period_date = period_date.replace(day=1)  # First day of month
            
            # Calculate end date (last day of month)
            if period_date.month == 12:
                end_date = period_date.replace(year=period_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = period_date.replace(month=period_date.month + 1, day=1) - timedelta(days=1)
            
            period_name = period_date.strftime('%B %Y')
            
            period = PayrollPeriod.objects.create(
                start_date=period_date,
                end_date=end_date,
                period_name=period_name,
                status=random.choice(['Paid', 'Paid', 'Approved', 'Processing']) if i > 0 else 'Processing'  # Current month processing
            )
            
            payroll_periods.append(period)
        
        self.stdout.write(f'✅ Created {len(payroll_periods)} payroll periods')
        return payroll_periods

    def seed_payrolls(self, employees, payroll_periods, users):
        """Seed payroll records"""
        self.stdout.write('💰 Creating payroll records...')
        
        payrolls_created = 0
        
        for employee in employees:
            # Get base salary from employee model (convert to Decimal)
            try:
                base_salary = Decimal(str(employee.salary))
            except:
                base_salary = Decimal('50000')  # Default salary
            
            for period in payroll_periods:
                # Skip if payroll already exists
                if Payroll.objects.filter(employee=employee, payroll_period=period).exists():
                    continue
                
                # Calculate salary components
                basic_salary = base_salary * Decimal('0.6')  # 60% basic
                
                # Allowances (percentages of basic)
                hra = basic_salary * Decimal('0.4')  # 40% HRA
                transport_allowance = Decimal(str(random.randint(1600, 3200)))
                medical_allowance = Decimal(str(random.randint(1250, 2500)))
                other_allowances = basic_salary * Decimal('0.1')  # 10% other
                
                # Overtime (random)
                overtime_hours = Decimal(str(random.randint(0, 20)))
                
                # Bonuses (performance-based)
                performance_bonus = basic_salary * Decimal(str(random.uniform(0, 0.2)))  # Up to 20%
                attendance_bonus = Decimal(str(random.randint(0, 2000)))
                project_bonus = basic_salary * Decimal(str(random.uniform(0, 0.1)))  # Up to 10%
                
                # Deductions
                pf = basic_salary * Decimal('0.12')  # 12% PF
                professional_tax = Decimal('200')
                income_tax = base_salary * Decimal(str(random.uniform(0.05, 0.20)))  # 5-20% tax
                health_insurance = Decimal(str(random.randint(500, 2000)))
                other_deductions = Decimal(str(random.randint(0, 1000)))
                
                # Determine status based on period
                if period.status == 'Paid':
                    payroll_status = 'Paid'
                elif period.status == 'Approved':
                    payroll_status = random.choice(['Approved', 'Paid'])
                else:
                    payroll_status = random.choice(['Draft', 'Calculated', 'Approved'])
                
                payroll = Payroll.objects.create(
                    employee=employee,
                    payroll_period=period,
                    basic_salary=basic_salary,
                    overtime_hours=overtime_hours,
                    house_rent_allowance=hra,
                    transport_allowance=transport_allowance,
                    medical_allowance=medical_allowance,
                    other_allowances=other_allowances,
                    performance_bonus=performance_bonus,
                    attendance_bonus=attendance_bonus,
                    project_bonus=project_bonus,
                    provident_fund=pf,
                    professional_tax=professional_tax,
                    income_tax=income_tax,
                    health_insurance=health_insurance,
                    other_deductions=other_deductions,
                    status=payroll_status,
                    processed_by=random.choice([u for u in users if u.role == 'HR']) if random.choice([True, False]) else None,
                    approved_by=random.choice([u for u in users if u.role in ['HR', 'MANAGER']]) if payroll_status in ['Approved', 'Paid'] else None
                )
                
                payrolls_created += 1
        
        self.stdout.write(f'✅ Created {payrolls_created} payroll records')

    def seed_performance_metrics(self, employees, payroll_periods):
        """Seed performance metrics"""
        self.stdout.write('📊 Creating performance metrics...')
        
        metrics_created = 0
        
        # Only create metrics for the last 3 periods
        recent_periods = payroll_periods[:3]
        
        for employee in random.sample(employees, min(len(employees), 40)):  # 40 employees with metrics
            for period in recent_periods:
                # Skip if metrics already exist
                if PerformanceMetric.objects.filter(employee=employee, period=period).exists():
                    continue
                
                # Generate realistic performance scores
                base_performance = random.uniform(60, 95)  # Base performance level
                
                PerformanceMetric.objects.create(
                    employee=employee,
                    period=period,
                    project_completion_rate=Decimal(str(random.uniform(base_performance - 10, min(100, base_performance + 15)))),
                    quality_score=Decimal(str(random.uniform(base_performance - 5, min(100, base_performance + 10)))),
                    attendance_percentage=Decimal(str(random.uniform(85, 100))),
                    client_feedback_score=Decimal(str(random.uniform(6, 10))),
                    team_collaboration_score=Decimal(str(random.uniform(6, 10))),
                    innovation_score=Decimal(str(random.uniform(5, 10)))
                )
                
                metrics_created += 1
        
        self.stdout.write(f'✅ Created {metrics_created} performance metrics')
