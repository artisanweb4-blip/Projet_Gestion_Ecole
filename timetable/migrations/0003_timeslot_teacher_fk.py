from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    """Associe chaque créneau existant au profil Teacher lié à l'ancien User."""
    TimeSlot = apps.get_model('timetable', 'TimeSlot')
    Teacher = apps.get_model('teachers', 'Teacher')
    for slot in TimeSlot.objects.exclude(teacher=None).only('id', 'teacher'):
        teacher = Teacher.objects.filter(user_id=slot.teacher_id).only('id').first()
        slot.temp_teacher_id = teacher.pk if teacher else None
        slot.save(update_fields=['temp_teacher'])


def backwards(apps, schema_editor):
    TimeSlot = apps.get_model('timetable', 'TimeSlot')
    for slot in TimeSlot.objects.exclude(temp_teacher=None).only('id', 'temp_teacher'):
        slot.teacher_id = slot.temp_teacher.user_id
        slot.save(update_fields=['teacher'])


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0002_classroom_school'),
        ('teachers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeslot',
            name='temp_teacher',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='timeslot_tmp', to='teachers.teacher', verbose_name='Enseignant (temp)'),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(
            model_name='timeslot',
            name='teacher',
        ),
        migrations.RenameField(
            model_name='timeslot',
            old_name='temp_teacher',
            new_name='teacher',
        ),
        migrations.AlterField(
            model_name='timeslot',
            name='teacher',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='time_slots', to='teachers.teacher', verbose_name='Enseignant'),
        ),
    ]
