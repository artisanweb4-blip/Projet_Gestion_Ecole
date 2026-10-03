"""
Rattachement des données existantes (installations mono-école) à l'école
principale : garantit que chaque établissement ne voit QUE ses données.
"""
from django.db import migrations


def backfill(apps, schema_editor):
    School = apps.get_model('accounts', 'School')
    SchoolSetting = apps.get_model('school_settings', 'SchoolSetting')
    User = apps.get_model('accounts', 'User')

    setting = SchoolSetting.objects.first()
    name = (setting.school_name if setting and setting.school_name else 'École principale')
    school, _ = School.objects.get_or_create(
        name=name,
        defaults={
            'address': (setting.address if setting else '') or '',
            'phone': (setting.phone if setting else '') or '',
            'email': (setting.email if setting else '') or '',
        },
    )

    MODELS = [
        ('students', 'Student'), ('teachers', 'Teacher'),
        ('classes', 'Class'), ('parents', 'Parent'),
        ('courses', 'Program'), ('courses', 'Subject'),
        ('grades', 'AcademicYear'), ('grades', 'Period'),
        ('timetable', 'Classroom'),
        ('school_calendar', 'EventCategory'),
        ('school_calendar', 'AcademicEvent'),
        ('admissions', 'AdmissionApplication'),
        ('documents', 'DocumentModele'),
    ]
    for app_label, model_name in MODELS:
        model = apps.get_model(app_label, model_name)
        model.objects.filter(school__isnull=True).update(school=school)

    User.objects.filter(school__isnull=True).update(school=school)

    if setting and setting.school_id is None:
        setting.school = school
        setting.save(update_fields=['school'])


def unbackfill(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_school_user_school'),
        ('admissions', '0003_admissionapplication_school'),
        ('classes', '0003_class_school'),
        ('courses', '0002_program_school_subject_school'),
        ('documents', '0002_documentmodele_school'),
        ('grades', '0002_academicyear_school_period_school'),
        ('parents', '0002_parent_school'),
        ('school_calendar', '0002_academicevent_school_eventcategory_school'),
        ('school_settings', '0002_schoolsetting_school'),
        ('students', '0003_student_school_alter_student_student_id_and_more'),
        ('teachers', '0002_teacher_school'),
        ('timetable', '0002_classroom_school'),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
