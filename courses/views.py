# courses/views.py

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from classes.models import Class as SchoolClass
from core.mixins import HtmxCrudMixin
from .forms import ProgramForm, ProgramSubjectFormSet
from .models import Program, ProgramSubject, Subject


# ==============================================================================
# VUES AJAX POUR LE CHARGEMENT DYNAMIQUE DES MATIÈRES
# ==============================================================================


def get_subjects_by_program(request):
    """
    Renvoie la liste des matières liées à un programme au format JSON.
    Utilisé pour mettre à jour dynamiquement le sélecteur de matières.
    """
    program_id = request.GET.get('program_id')
    subjects_data = []

    if program_id:
        program_subjects = ProgramSubject.objects.filter(
            program_id=program_id
        ).select_related('subject')
        for ps in program_subjects:
            subjects_data.append(
                {
                    'id': ps.subject.id,
                    'name': ps.subject.name,
                    'code': ps.subject.code or '',
                    'coefficient': float(ps.coefficient),
                    'total_hours': ps.total_hours,
                }
            )

    return JsonResponse({'subjects': subjects_data})


def ajax_get_subjects_by_class(request):
    class_id = request.GET.get('class_id')
    subjects_data = []

    if class_id and class_id.isdigit():
        try:
            school_class = SchoolClass.objects.select_related('program').get(id=int(class_id))

            if school_class.program:
                program_subjects = ProgramSubject.objects.filter(
                    program=school_class.program
                ).select_related('subject')

                subjects_data = [
                    {
                        'id': ps.subject.id,
                        'name': ps.subject.name,
                        'code': getattr(ps.subject, 'code', '') or '',
                    }
                    for ps in program_subjects
                ]
        except SchoolClass.DoesNotExist:
            pass

    return JsonResponse({'subjects': subjects_data})

# ==============================================================================
# VUES POUR LES PROGRAMMES (PROGRAM)
# ==============================================================================


class ProgramListView(ListView):
    """
    Affiche la liste de tous les programmes d'études avec recherche et pagination.
    """

    model = Program
    template_name = 'courses/program_list.html'
    context_object_name = 'programs'
    paginate_by = 12

    def get_queryset(self):
        queryset = Program.objects.all().order_by('name')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(name__icontains=q) | queryset.filter(
                code__icontains=q
            )
        return queryset


class ProgramDetailView(DetailView):
    """
    Affiche les détails d'un programme spécifique avec ses matières associées.
    """

    model = Program
    template_name = 'courses/program_detail.html'
    context_object_name = 'program'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupération directe des objets ProgramSubject liés à ce programme
        context['program_subjects'] = ProgramSubject.objects.filter(
            program=self.object
        ).select_related('subject', 'teacher')
        return context


class ProgramCreateView(HtmxCrudMixin, CreateView):
    """
    Permet de créer un nouveau programme avec ses matières (FormSet).
    """

    model = Program
    form_class = ProgramForm
    template_name = 'courses/program_form.html'
    success_url = reverse_lazy('courses:program_list')
    partial_template = 'courses/program_form_modal.html'
    modal_title = 'Nouveau programme'
    add_success_message = False  # la vue ajoute déjà son message

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['formset'] = ProgramSubjectFormSet(self.request.POST)
        else:
            data['formset'] = ProgramSubjectFormSet()
        data['title'] = 'Nouveau Programme'
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(
                self.request,
                "Le programme et ses matières ont été créés avec succès.",
            )
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ProgramUpdateView(HtmxCrudMixin, UpdateView):
    """
    Permet de modifier un programme existant et ses matières associées.
    """

    model = Program
    form_class = ProgramForm
    template_name = 'courses/program_form.html'
    success_url = reverse_lazy('courses:program_list')
    partial_template = 'courses/program_form_modal.html'
    modal_title = 'Modifier le programme'
    add_success_message = False  # la vue ajoute déjà son message

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['formset'] = ProgramSubjectFormSet(
                self.request.POST, instance=self.object
            )
        else:
            data['formset'] = ProgramSubjectFormSet(instance=self.object)
        data['title'] = 'Modifier le Programme'
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(
                self.request, "Le programme a été mis à jour avec succès."
            )
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ProgramDeleteView(HtmxCrudMixin, DeleteView):
    """
    Permet de supprimer un programme d'études.
    """

    model = Program
    template_name = 'courses/program_confirm_delete.html'
    success_url = reverse_lazy('courses:program_list')
    partial_template = 'includes/delete_modal.html'
    modal_title = 'Supprimer ce programme'
    success_message = 'Programme supprimé.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program_subjects'] = ProgramSubject.objects.filter(
            program=self.object
        )
        return context


# ==============================================================================
# VUES POUR LES MATIÈRES (SUBJECT)
# ==============================================================================


class SubjectListView(ListView):
    """
    Affiche la liste des matières/cours.
    """

    model = Subject
    template_name = 'courses/subject_list.html'
    context_object_name = 'subjects'
    paginate_by = 10


class SubjectCreateView(CreateView):
    """
    Permet d'ajouter une nouvelle matière.
    """

    model = Subject
    fields = ['name', 'code', 'description']
    template_name = 'courses/subject_form.html'
    success_url = reverse_lazy('courses:subject_list')