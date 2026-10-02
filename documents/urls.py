from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Page principale des documents
    path('', views.index_documents, name='index'),

    # Exemplaire PDF de démonstration par type
    path('catalogue/<str:key>/exemple/', views.document_sample_pdf, name='document_sample'),

    # Génération des certificats & attestations
    path('certificat-scolarite/', views.generate_certificat_scolarite, name='generate_certificat_scolarite'),
    path('certificat-frequentation/', views.generate_certificat_frequentation, name='generate_certificat_frequentation'),
    path('certificat-transfert/', views.generate_certificat_transfert, name='generate_certificat_transfert'),

    # Documents Pédagogiques & Classes
    path('registre-presence/', views.registre_presence, name='registre_presence'),

    # RH & Demandes
    path('demande-conge/', views.demande_conge_create, name='demande_conge_create'),
]