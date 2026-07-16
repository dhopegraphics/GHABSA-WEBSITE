# Generated manually for renaming level to year

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0007_academicslides_academics_a_course__9cf918_idx_and_more'),
    ]

    operations = [
        # First remove the old index that references 'level'
        migrations.RemoveIndex(
            model_name='course',
            name='academics_c_level_e326bb_idx',
        ),
        # Rename the field from level to year
        migrations.RenameField(
            model_name='course',
            old_name='level',
            new_name='year',
        ),
        # Add help_text to the year field
        migrations.AlterField(
            model_name='course',
            name='year',
            field=models.IntegerField(help_text='Year 1, 2, 3, or 4'),
        ),
        # Add the new index with 'year' instead of 'level'
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['year', 'semester'], name='academics_c_year_e326bb_idx'),
        ),
    ]
