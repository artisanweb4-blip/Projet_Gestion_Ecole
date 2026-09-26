from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DocumentModele, DemandeConge
from .forms import CertificatScolariteForm, DemandeCongeForm


def index_documents(request):
    """
    Vue principale affichant l'ensemble de la page Documents (votre dashboard)
    """
    modeles = DocumentModele.objects.filter(est_actif=True)
    
    context = {
        'modeles_rh': modeles.filter(categorie='RH'),
        'modeles_admin': modeles.filter(categorie='ADMINISTRATIF'),
        'modeles_pedagogy': modeles.filter(categorie='PEDAGOGIQUE'),
    }
    return render(request, 'documents/documents_list.html', context)


def generate_certificat_scolarite(request):
    """
    Génération du Certificat de Scolarité
    """
    if request.method == 'POST':
        form = CertificatScolariteForm(request.POST)
        if form.is_valid():
            context = {
                'eleve': {
                    'nom': form.cleaned_data['eleve_nom'],
                    'prenom': form.cleaned_data['eleve_prenom'],
                    'matricule': form.cleaned_data['matricule'],
                    'date_naissance': form.cleaned_data['date_naissance'].strftime('%d/%m/%Y'),
                    'classe': form.cleaned_data['classe'],
                },
                'annee_scolaire': form.cleaned_data['annee_scolaire'],
                'numero_reference': "2026/CS-0042",
            }
            # Rend directement le template imprimable/PDF
            return render(request, 'documents/certificat_scolarite_pdf.html', context)
    else:
        form = CertificatScolariteForm()

    return render(request, 'documents/form_certificat.html', {'form': form, 'titre': 'Certificat de Scolarité'})


def generate_certificat_frequentation(request):
    """
    Exemple de génération pour le certificat de fréquentation
    """
    # Adaptable selon la structure du certificat de fréquentation
    return render(request, 'documents/certificat_frequentation_pdf.html')


def generate_certificat_transfert(request):
    """
    Exemple de génération pour le certificat d'abandon / transfert
    """
    return render(request, 'documents/certificat_transfert_pdf.html')


def registre_presence(request):
    """
    Vue d'affichage ou d'impression du registre d'appel par classe
    """
    return render(request, 'documents/registre_presence_pdf.html')


@login_required
def demande_conge_create(request):
    """
    Soumettre une demande de congé/autorisation d'absence
    """
    if request.method == 'POST':
        form = DemandeCongeForm(request.POST)
        if form.is_valid():
            conge = form.save(commit=False)
            conge.employe = request.user
            conge.save()
            messages.success(request, "Votre demande de congé a été enregistrée avec succès.")
            return redirect('documents:index')
    else:
        form = DemandeCongeForm()

    return render(request, 'documents/demande_conge_form.html', {'form': form})