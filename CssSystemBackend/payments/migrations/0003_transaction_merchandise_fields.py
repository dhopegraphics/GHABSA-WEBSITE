# Generated migration for adding merchandise tracking fields to Transaction

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_allow_anonymous_transactions'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='merchandise_validation_code',
            field=models.CharField(
                blank=True,
                help_text='Validation code for merchandise pickup',
                max_length=10,
                null=True,
                unique=True
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='merchandise_collected',
            field=models.BooleanField(
                default=False,
                help_text='Whether merchandise has been collected'
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='merchandise_collected_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When merchandise was collected',
                null=True
            ),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(
                fields=['merchandise_validation_code'],
                name='payments_tr_merchan_idx'
            ),
        ),
    ]
