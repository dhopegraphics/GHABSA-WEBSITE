"""
Management command to backfill audit logs for existing expenses.
Usage: python manage.py backfill_expense_audit_logs
"""
from django.core.management.base import BaseCommand
from payments.models import Expense, ExpenseAuditLog


class Command(BaseCommand):
    help = 'Backfill audit logs for existing expenses that have no audit history'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Create audit logs for ALL expenses (including those with existing logs)',
        )

    def handle(self, *args, **options):
        include_all = options.get('all', False)
        
        if include_all:
            expenses = Expense.objects.all()
            self.stdout.write(self.style.WARNING('Creating audit logs for ALL expenses...'))
        else:
            # Get expenses that have no audit logs
            expenses_with_logs = ExpenseAuditLog.objects.values_list('expense_id', flat=True).distinct()
            expenses = Expense.objects.exclude(id__in=expenses_with_logs)
            self.stdout.write(f'Found {expenses.count()} expenses without audit logs...')
        
        created_count = 0
        
        for expense in expenses:
            # Create a "created" audit log entry
            ExpenseAuditLog.objects.create(
                expense=expense,
                action='created',
                performed_by=expense.created_by,
                new_values={
                    'title': expense.title,
                    'reference': expense.reference,
                    'amount': str(expense.amount),
                    'status': expense.status,
                    'category': expense.category.name if expense.category else None,
                    'recipient': expense.recipient.name if expense.recipient else expense.recipient_name,
                    'expense_date': str(expense.expense_date),
                },
                comments='Initial audit log (backfilled)',
            )
            created_count += 1
            self.stdout.write(f'  ✅ {expense.reference}: {expense.title}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done! Created {created_count} audit log entries.'))
