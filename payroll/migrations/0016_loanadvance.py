from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('hr_management', '0011_employee_pan'),
        ('payroll', '0015_salarycomponentauditlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoanAdvance',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('loan_type', models.CharField(choices=[('Loan', 'Loan'), ('Advance', 'Advance')], default='Loan', max_length=20)),
                ('principal_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('emi_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('outstanding_balance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('tenure_months', models.PositiveIntegerField(default=12)),
                ('disbursed_date', models.DateField()),
                ('next_deduction_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Active', 'Active'), ('Closed', 'Closed'), ('Paused', 'Paused')], default='Active', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loan_advances', to='hr_management.employee')),
            ],
            options={
                'verbose_name': 'LoanAdvance',
                'verbose_name_plural': 'LoanAdvances',
                'ordering': ['-created_at'],
            },
        ),
    ]
