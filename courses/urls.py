from django.urls import path
from . import views

# Espace de nommage de l'application (permet d'utiliser 'courses:program_list' dans les templates)
app_name = 'courses'

urlpatterns = [
    # ==========================================================================
    # ROUTES POUR LES PROGRAMMES (PROGRAM)
    # ==========================================================================
    # Liste des programmes : /courses/
    path('', views.ProgramListView.as_view(), name='program_list'),
    
    # Création d'un programme : /courses/create/
    path('create/', views.ProgramCreateView.as_view(), name='program_create'),
    
    # Détails d'un programme : /courses/1/
    path('<int:pk>/', views.ProgramDetailView.as_view(), name='program_detail'),
    
    # Modification d'un programme : /courses/1/update/
    path('<int:pk>/update/', views.ProgramUpdateView.as_view(), name='program_update'),
    
    # Suppression d'un programme : /courses/1/delete/
    path('<int:pk>/delete/', views.ProgramDeleteView.as_view(), name='program_delete'),

    # ==========================================================================
    # ROUTES POUR LES MATIÈRES (SUBJECT)
    # ==========================================================================
    # Liste des matières : /courses/subjects/
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    
    # Création d'une matière : /courses/subjects/create/
    path('subjects/create/', views.SubjectCreateView.as_view(), name='subject_create'),
    path(
        'ajax/get-subjects-by-class/', 
        views.ajax_get_subjects_by_class, 
        name='ajax_get_subjects_by_class'
    ),

    path(
        'api/get-subjects-by-program/',
        views.get_subjects_by_program,
        name='ajax_get_subjects_by_program',
    ),
]