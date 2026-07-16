# Create this file: accounts/migrations/0005_add_analytics_permission.py

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_customuser_current_semester_customuser_gender_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={
                'verbose_name': 'Account',
                'permissions': [
                    ('view_sensitive_student_data', 'Can view sensitive student information (emails, student ID, index number)'),
                    ('view_accounts_analytics', 'Can view accounts analytics dashboard'),
                ],
            },
        ),
    ]