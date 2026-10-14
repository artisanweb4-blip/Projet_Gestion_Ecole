from django.db import migrations


def fix_missing_school(apps, schema_editor):
    """Répare les programmes et matières créés sans école (school=NULL).

    Contexte : le formulaire « programme + matières » créait les matières
    sans les rattacher à l'école ; ces matières étaient invisibles du filtre
    automatique par école (emploi du temps notamment). On déduit l'école :
    1. pour un programme : via une classe liée, sinon l'unique école ;
    2. pour une matière : via un programme lié, sinon l'unique école.
    Si une matière équivalente existe déjà dans l'école cible, les liens
    (ProgramSubject) sont reversés vers elle et le doublon orphelin supprimé.
    """
    School = apps.get_model('accounts', 'School')
    Program = apps.get_model('courses', 'Program')
    Subject = apps.get_model('courses', 'Subject')
    ProgramSubject = apps.get_model('courses', 'ProgramSubject')
    Class = apps.get_model('classes', 'Class')

    schools = list(School.objects.all())
    unique_school = schools[0] if len(schools) == 1 else None

    # 1) Programmes sans école
    for program in Program.objects.filter(school__isnull=True):
        target = None
        link = (
            Class.objects.filter(program_id=program.pk)
            .exclude(school__isnull=True)
            .values_list('school_id', flat=True)
            .first()
        )
        if link:
            target = link
        elif unique_school is not None:
            target = unique_school.pk
        if target is not None:
            Program.objects.filter(pk=program.pk).update(school_id=target)

    # 2) Matières sans école
    for subject in Subject.objects.filter(school__isnull=True):
        target = None
        link = (
            ProgramSubject.objects.filter(subject_id=subject.pk)
            .exclude(program__school__isnull=True)
            .values_list('program__school_id', flat=True)
            .first()
        )
        if link:
            target = link
        elif unique_school is not None:
            target = unique_school.pk
        if target is None:
            continue

        twin = (
            Subject.objects.filter(school_id=target, name=subject.name)
            .exclude(pk=subject.pk)
            .values_list('pk', flat=True)
            .first()
        )
        if twin:
            # Reverser les liens vers la matière déjà rattachée, supprimer l'orphelin
            ProgramSubject.objects.filter(subject_id=subject.pk).update(subject_id=twin)
            Subject.objects.filter(pk=subject.pk).delete()
        else:
            Subject.objects.filter(pk=subject.pk).update(school_id=target)


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_program_school_subject_school'),
        ('classes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fix_missing_school, migrations.RunPython.noop),
    ]
