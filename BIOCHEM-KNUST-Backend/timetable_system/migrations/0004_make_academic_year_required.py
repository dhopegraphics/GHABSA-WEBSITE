from django.db import migrations, models


def compute_default_academic_year():
    from django.utils import timezone

    today = timezone.now().date()
    if today.month <= 9:
        start = today.year - 1
    else:
        start = today.year
    return f"{start}/{start+1}"


def forwards(apps, schema_editor):
    ClassSchedule = apps.get_model("timetable_system", "ClassSchedule")
    default = compute_default_academic_year()
    # Backfill NULL or empty values
    ClassSchedule.objects.filter(academic_year__isnull=True).update(academic_year=default)
    ClassSchedule.objects.filter(academic_year="").update(academic_year=default)


def backwards(apps, schema_editor):
    # no-op: don't clear values on reverse
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("timetable_system", "0003_classschedule_academic_year"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name="classschedule",
            name="academic_year",
            field=models.CharField(max_length=9),
        ),
    ]
