# Generated migration for ProductAudit model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('products', '0028_add_academic_year_tracking'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductAudit',
            fields=[
                ('audit_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action', models.CharField(choices=[('create', 'Product Created'), ('update', 'Product Updated'), ('delete', 'Product Deleted'), ('price_change', 'Price Changed'), ('stock_change', 'Stock Changed'), ('status_change', 'Status Changed')], max_length=20)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('old_values', models.JSONField(blank=True, default=dict, help_text='Previous field values before change')),
                ('new_values', models.JSONField(blank=True, default=dict, help_text='New field values after change')),
                ('changed_fields', models.JSONField(blank=True, default=list, help_text='List of fields that were changed')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, help_text='Additional notes about the change')),
                ('changed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_changes', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='products.product')),
            ],
            options={
                'verbose_name': 'Product Audit Log',
                'verbose_name_plural': 'Product Audit Logs',
                'db_table': 'product_audit',
                'ordering': ['-changed_at'],
            },
        ),
    ]
