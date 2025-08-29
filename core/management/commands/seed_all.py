from django.core.management.base import BaseCommand
from django.db import transaction
import random
from datetime import date, timedelta
from faker import Faker

# Import all your models
from authentication.models.user import User
from hr_management.models.hr_management_models import Employee, LeaveRequest, LeaveBalance, Attendance
from company.models.company_model import Company
from department.models.department_model import Department
from projects.models.project_model import Project, UserMapping, ManagerMapping, Milestone
from projects.models.epic_model import Epic
from projects.models.sprint_model import Sprint
from projects.models.task_model import Task
from projects.models.comments_model import Comment
from teams.models.team_model import Team
from teams.models.team_members_mapping import TeamMembersMapping
from time_tracking.models.time_tracking_models import TimeEntry
from ai_insights.models.ai_models import AIRecommendation, ProjectHealthMetric, AIInsight

fake = Faker()

class Command(BaseCommand):
    help = 'Seed database with comprehensive fake data'

    def add_arguments(self, parser):
        parser.add_argument('--companies', type=int, default=3, help='Number of companies')
        parser.add_argument('--users', type=int, default=15, help='Users per company')
        parser.add_argument('--projects', type=int, default=5, help='Projects per company')
        parser.add_argument('--clear', action='store_true', help='Clear existing data')

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_data()

        with transaction.atomic():
            companies = self.seed_companies(options['companies'])
            departments = self.seed_departments(companies)
            users, employees = self.seed_users_and_employees(companies, departments, options['users'])
            projects = self.seed_projects(companies, employees, options['projects'])
            teams = self.seed_teams(companies, projects, users)
            self.seed_epics_sprints_tasks(projects, users)
            self.seed_time_tracking(users)
            self.seed_ai_data(projects, users)
            self.seed_hr_data(employees)

        self.stdout.write(self.style.SUCCESS('✅ Database seeding completed successfully!'))

    def clear_data(self):
        """Clear existing data in correct order"""
        self.stdout.write('🗑️ Clearing existing data...')
        
        # Clear in order to avoid FK constraint issues
        AIRecommendation.objects.all().delete()
        AIInsight.objects.all().delete()
        ProjectHealthMetric.objects.all().delete()
        TimeEntry.objects.all().delete()
        Comment.objects.all().delete()
        Task.objects.all().delete()
        Sprint.objects.all().delete()
        Epic.objects.all().delete()
        Milestone.objects.all().delete()
        TeamMembersMapping.objects.all().delete()
        Team.objects.all().delete()
        UserMapping.objects.all().delete()
        ManagerMapping.objects.all().delete()
        Project.objects.all().delete()
        Attendance.objects.all().delete()
        LeaveRequest.objects.all().delete()
        LeaveBalance.objects.all().delete()
        Employee.objects.all().delete()
        Department.objects.all().delete()
        Company.objects.all().delete()
        User.objects.all().delete()
        
        self.stdout.write('✅ Data cleared successfully!')

    def seed_companies(self, num_companies):
        """Seed companies with realistic data"""
        self.stdout.write(f'🏢 Creating {num_companies} companies...')
        companies = []
        
        company_names = [
            'TechNova Solutions', 'InnovateCorp', 'Digital Dynamics',
            'FutureSoft Labs', 'AgileWorks Inc', 'CodeCraft Studios'
        ]
        
        for i in range(num_companies):
            company = Company.objects.create(
                name=company_names[i] if i < len(company_names) else fake.company(),
                description=fake.catch_phrase()
            )
            companies.append(company)
            
        self.stdout.write(f'✅ Created {len(companies)} companies')
        return companies

    # In your seed_all.py file, update the seed_departments method:

    def seed_departments(self, companies):
        """Seed departments for each company"""
        self.stdout.write('🏛️ Creating departments...')
        departments = []
        
        dept_names = [
            'Engineering', 'Human Resources', 'Marketing', 'Sales',
            'Product Management', 'Quality Assurance', 'DevOps', 'Design'
        ]
        
        for company in companies:
            for dept_name in random.sample(dept_names, min(5, len(dept_names))):
                # Use get_or_create to avoid duplicates
                dept, created = Department.objects.get_or_create(
                    name=dept_name,
                    defaults={
                        'description': f'{dept_name} department for {company.name}'
                    }
                )
                departments.append(dept)
                
                if created:
                    self.stdout.write(f'✅ Created department: {dept_name}')
                else:
                    self.stdout.write(f'ℹ️ Department already exists: {dept_name}')
                    
        self.stdout.write(f'✅ Processed {len(departments)} departments')
        return departments


    
    
    def seed_users_and_employees(self, companies, departments, users_per_company):
        """Seed users with only HR, MANAGER, and EMPLOYEE roles"""
        self.stdout.write(f'👥 Creating {users_per_company} users per company with HR, MANAGER, EMPLOYEE roles only...')
        users = []
        employees = []
        
        for company in companies:
            company_depts = departments[:5]  # Limit departments per company
            
            # Guarantee at least one HR and one MANAGER per company
            guaranteed_roles = ['HR', 'MANAGER']
            remaining_slots = users_per_company - len(guaranteed_roles)
            
            # Fill remaining slots with EMPLOYEE role only
            additional_roles = ['EMPLOYEE'] * remaining_slots
            
            # Combine guaranteed and additional roles
            all_roles = guaranteed_roles + additional_roles
            
            # Shuffle to randomize order
            random.shuffle(all_roles)
            
            for i, role in enumerate(all_roles):
                username = f'user{i}_{company.name.lower().replace(" ", "")}'
                email = f'{username}@{company.name.lower().replace(" ", "")}.com'
                
                # Role-specific naming and designations
                if role == 'HR':
                    name = f'HR Manager - {fake.first_name()} {fake.last_name()}'
                    designation = 'Human Resources Manager'
                elif role == 'MANAGER':
                    name = f'Project Manager - {fake.first_name()} {fake.last_name()}'
                    designation = 'Project Manager'
                else:  # EMPLOYEE
                    name = f'{fake.first_name()} {fake.last_name()}'
                    designation = fake.job()
                
                user = User.objects.create_user(
                    email=email,
                    name=name,
                    username=username,
                    password='password123',
                    role=role,
                    date_of_birth=fake.date_of_birth(minimum_age=22, maximum_age=65)
                )
                
                employee = Employee.objects.create(
                    user=user,
                    company=company,
                    department=random.choice(company_depts),
                    salary=str(random.randint(40000, 150000)),
                    date_of_joining=fake.date_between(start_date='-3y', end_date='today'),
                    designation=designation,
                    phone=fake.phone_number()[:15]
                )
                
                users.append(user)
                employees.append(employee)
                
                # Create leave balance
                LeaveBalance.objects.create(
                    employee=employee,
                    balance=random.randint(15, 30)
                )
            
            # Log role distribution for this company
            company_roles = [u.role for u in users if any(e.company == company and e.user == u for e in employees)]
            role_count = {role: company_roles.count(role) for role in ['HR', 'MANAGER', 'EMPLOYEE']}
            
            self.stdout.write(f'✅ {company.name}: HR={role_count["HR"]}, MANAGER={role_count["MANAGER"]}, EMPLOYEE={role_count["EMPLOYEE"]}')
        
        # Overall summary
        all_roles = [user.role for user in users]
        total_role_count = {role: all_roles.count(role) for role in ['HR', 'MANAGER', 'EMPLOYEE']}
        
        self.stdout.write(f'✅ Total users created: {len(users)}')
        self.stdout.write(f'✅ Overall distribution: HR={total_role_count["HR"]}, MANAGER={total_role_count["MANAGER"]}, EMPLOYEE={total_role_count["EMPLOYEE"]}')
        
        return users, employees


    def seed_projects(self, companies, employees, projects_per_company):
        """Seed projects with realistic data"""
        self.stdout.write('📁 Creating projects...')
        projects = []
        
        project_types = [
            'E-commerce Platform', 'Mobile App Development', 'Web Application',
            'API Development', 'Data Analytics Dashboard', 'CRM System',
            'ERP Solution', 'AI/ML Platform', 'Cloud Migration', 'Security Audit'
        ]
        
        for company in companies:
            company_employees = [e for e in employees if e.company == company]
            managers = [e for e in company_employees if e.user.role in ['MANAGER', 'ADMIN']]
            
            if not managers:
                continue
                
            for i in range(projects_per_company):
                project_name = f'{random.choice(project_types)} {i+1}'
                
                project = Project.objects.create(
                    name=project_name,
                    description=fake.text(max_nb_chars=300),
                    manager=random.choice(managers),
                    status=random.choice(['Planning', 'Ongoing', 'Completed', 'On Hold']),
                    start_date=fake.date_between(start_date='-1y', end_date='today'),
                    end_date=fake.date_between(start_date='today', end_date='+6m'),
                    color_scheme=fake.hex_color(),
                    ai_health_score=random.randint(60, 95),
                    priority=random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
                )
                projects.append(project)
                
                # Assign team members
                team_size = random.randint(3, 8)
                project_team = random.sample(company_employees, min(team_size, len(company_employees)))
                
                for emp in project_team:
                    UserMapping.objects.create(employee=emp, project=project)
                
                # Create manager mapping
                ManagerMapping.objects.create(manager=project.manager, project=project)
                
                # Create milestones
                for j in range(random.randint(2, 5)):
                    Milestone.objects.create(
                        title=f'Milestone {j+1}: {fake.bs().title()}',
                        description=fake.text(max_nb_chars=200),
                        project=project,
                        status=random.choice(['PENDING', 'IN_PROGRESS', 'COMPLETED']),
                        target_date=fake.date_between(start_date='today', end_date='+3m'),
                        completion_percentage=random.randint(0, 100)
                    )
        
        self.stdout.write(f'✅ Created {len(projects)} projects')
        return projects

    def seed_teams(self, companies, projects, users):
        """Seed teams and team memberships"""
        self.stdout.write('👥 Creating teams...')
        teams = []
        
        for company in companies:
            company_projects = [p for p in projects if p.manager.company == company]
            if not company_projects:
                continue
                
            for i in range(3):  # 3 teams per company
                team = Team.objects.create(
                    name=f'{company.name} Team {i+1}'
                )
                
                # Associate with projects
                team_projects = random.sample(company_projects, min(3, len(company_projects)))
                team.project_id.set(team_projects)
                teams.append(team)
                
                # Add team members
                team_members = random.sample(users, min(7, len(users)))
                for member in team_members:
                    TeamMembersMapping.objects.create(user=member, team=team)
        
        self.stdout.write(f'✅ Created {len(teams)} teams')
        return teams

    def seed_epics_sprints_tasks(self, projects, users):
        """Seed epics, sprints, and tasks"""
        self.stdout.write('📋 Creating epics, sprints, and tasks...')
        
        task_titles = [
            'Implement user authentication', 'Create dashboard UI', 'Setup database schema',
            'Develop API endpoints', 'Write unit tests', 'Deploy to staging',
            'Fix login bug', 'Optimize database queries', 'Add search functionality',
            'Implement notifications', 'Create user profile page', 'Setup CI/CD pipeline'
        ]
        
        for project in projects:
            # Create epics
            epics = []
            for i in range(random.randint(2, 4)):
                epic = Epic.objects.create(
                    project=project,
                    name=f'Epic {i+1}: {fake.catch_phrase()}',
                    description=fake.text(max_nb_chars=200),
                    color=fake.hex_color()
                )
                epics.append(epic)
            
            # Create sprints
            sprints = []
            start_date = date.today() - timedelta(days=120)
            
            for i in range(random.randint(3, 6)):
                sprint = Sprint.objects.create(
                    project=project,
                    name=f'{project.name} Sprint {i+1}',
                    description=f'Sprint {i+1} for {project.name}',
                    start_date=start_date + timedelta(days=i*14),
                    end_date=start_date + timedelta(days=(i+1)*14 - 1),
                    status=random.choice(['PLANNED', 'ACTIVE', 'COMPLETED']),
                    goal=fake.sentence(),
                    velocity=random.randint(15, 40),
                    ai_completion_probability=random.randint(70, 95)
                )
                sprints.append(sprint)
            
            # Create tasks
            for sprint in sprints:
                for _ in range(random.randint(8, 15)):
                    task = Task.objects.create(
                        project=project,
                        sprint=sprint,
                        epic=random.choice(epics) if epics and random.choice([True, False]) else None,
                        title=random.choice(task_titles),
                        description=fake.text(max_nb_chars=250),
                        status=random.choice(['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE', 'BLOCKED']),
                        priority=random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
                        task_type=random.choice(['STORY', 'BUG', 'TASK', 'SUBTASK']),
                        story_points=random.randint(1, 8),
                        assigned_to=random.choice(users) if random.choice([True, False]) else None,
                        due_date=fake.date_time_between(start_date='now', end_date='+30d'),
                        labels=['frontend', 'backend', 'api', 'ui', 'testing'][0:random.randint(0,3)],
                        progress_percentage=random.randint(0, 100)
                    )
                    
                    # Create comments
                    for _ in range(random.randint(1, 4)):
                        Comment.objects.create(
                            content=fake.paragraph(nb_sentences=random.randint(1, 3)),
                            comment_by=random.choice(users),
                            task=task
                        )

    def seed_time_tracking(self, users):
        """Seed time tracking entries"""
        self.stdout.write('⏰ Creating time tracking entries...')
        
        for user in random.sample(users, min(10, len(users))):
            for _ in range(random.randint(5, 15)):
                TimeEntry.objects.create(
                    user=user,
                    duration=timedelta(hours=random.randint(1, 8)),
                    date=fake.date_between(start_date='-30d', end_date='today'),
                    description=fake.sentence()
                )

    def seed_ai_data(self, projects, users):
        """Seed AI recommendations and health metrics"""
        self.stdout.write('🤖 Creating AI data...')
        
        recommendation_titles = [
            'Optimize team workload distribution',
            'Implement automated testing pipeline',
            'Hire additional frontend developer',
            'Upgrade development infrastructure',
            'Improve code review process',
            'Conduct team training session'
        ]
        
        for project in projects:
            # AI recommendations
            for _ in range(random.randint(2, 5)):
                AIRecommendation.objects.create(
                    title=random.choice(recommendation_titles),
                    description=fake.text(max_nb_chars=300),
                    recommendation_type=random.choice(['reallocation', 'hiring', 'optimization', 'risk_mitigation']),
                    impact=random.choice(['high', 'medium', 'low']),
                    severity=random.choice(['critical', 'warning', 'info']),
                    confidence=random.randint(60, 95),
                    project=project,
                    created_by=random.choice(users),
                    is_applied=random.choice([True, False])
                )
            
            # Project health metrics
            ProjectHealthMetric.objects.create(
                project=project,
                overall_score=random.randint(60, 95),
                timeline_risk=random.randint(10, 60),
                resource_risk=random.randint(15, 50),
                quality_risk=random.randint(10, 40),
                budget_risk=random.randint(20, 55),
                team_efficiency=random.randint(70, 95),
                risk_level=random.choice(['low', 'medium', 'high']),
                last_analyzed_by=random.choice(users)
            )

    def seed_hr_data(self, employees):
        """Seed HR-related data"""
        self.stdout.write('📋 Creating HR data...')
        
        # Leave requests
        for employee in random.sample(employees, min(20, len(employees))):
            for _ in range(random.randint(1, 4)):
                start_date = fake.date_between(start_date='-60d', end_date='+30d')
                LeaveRequest.objects.create(
                    employee=employee,
                    start_date=start_date,
                    end_date=start_date + timedelta(days=random.randint(1, 7)),
                    reason=fake.sentence(),
                    status=random.choice(['PENDING', 'APPROVED', 'REJECTED'])
                )
        
        # Attendance records
        for employee in random.sample(employees, min(15, len(employees))):
            for i in range(random.randint(10, 30)):
                attendance_date = date.today() - timedelta(days=i)
                if random.choice([True, False, True, True]):  # 75% attendance
                    Attendance.objects.create(
                        employee=employee,
                        date=attendance_date,
                        in_time=fake.time_object(),
                        out_time=fake.time_object()
                    )
