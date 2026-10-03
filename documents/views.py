from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa

from .models import DocumentModele, DemandeConge
from .forms import CertificatScolariteForm, DemandeCongeForm

# ---------------------------------------------------------------------------
# Catalogue des documents : un exemplaire PDF est disponible pour chaque type.
# ---------------------------------------------------------------------------
DOCUMENTS_CATALOG = [
    {
        'key': 'certificat_scolarite',
        'title': 'Certificat de scolarité',
        'description': "Atteste qu'un élève est régulièrement inscrit dans l'établissement.",
        'icon': 'fa-file-signature', 'color': '#059669',
        'generate_url': '/documents/certificat-scolarite/',
        'category': 'Administratif',
    },
    {
        'key': 'certificat_frequentation',
        'title': 'Certificat de fréquentation',
        'description': "Confirme la présence régulière de l'élève durant l'année.",
        'icon': 'fa-user-check', 'color': '#2563eb',
        'generate_url': '/documents/certificat-frequentation/',
        'category': 'Administratif',
    },
    {
        'key': 'certificat_transfert',
        'title': "Certificat de transfert",
        'description': "Délivré lorsqu'un élève quitte l'établissement pour une autre école.",
        'icon': 'fa-right-left', 'color': '#7c3aed',
        'generate_url': '/documents/certificat-transfert/',
        'category': 'Administratif',
    },
    {
        'key': 'attestation_reussite',
        'title': "Attestation de réussite",
        'description': "Officialise la réussite de l'élève à l'issue de l'année académique.",
        'icon': 'fa-award', 'color': '#d97706',
        'sample_only': True,
        'category': 'Administratif',
    },
    {
        'key': 'tableau_honneur',
        'title': 'Tableau d’honneur',
        'description': "Récompense les élèves ayant obtenu d'excellents résultats.",
        'icon': 'fa-medal', 'color': '#dc2626',
        'sample_only': True,
        'category': 'Pédagogique',
    },
    {
        'key': 'registre_presence',
        'title': 'Registre de présence',
        'description': 'Feuille d’émargement des présences pour une classe.',
        'icon': 'fa-clipboard-list', 'color': '#0f766e',
        'generate_url': '/documents/registre-presence/',
        'category': 'Pédagogique',
    },
    {
        'key': 'convocation_parent',
        'title': 'Convocation des parents',
        'description': 'Convoque officiellement un parent pour un entretien.',
        'icon': 'fa-envelope-open-text', 'color': '#b45309',
        'sample_only': True,
        'category': 'Administratif',
    },
    {
        'key': 'recu_paiement',
        'title': 'Reçu de paiement',
        'description': 'Justificatif numéroté des frais réglés par le parent.',
        'icon': 'fa-receipt', 'color': '#059669',
        'sample_only': True,
        'category': 'Financier',
    },
    {
        'key': 'bulletin',
        'title': 'Bulletin de notes',
        'description': 'Moyennes, coefficients, rang et appréciations de la période.',
        'icon': 'fa-file-lines', 'color': '#2563eb',
        'generate_url': '/grades/bulletins/',
        'category': 'Pédagogique',
    },
    {
        'key': 'demande_conge',
        'title': "Demande de congé (personnel)",
        'description': 'Formulaire de demande de congé pour le personnel.',
        'icon': 'fa-plane-departure', 'color': '#7c3aed',
        'generate_url': '/documents/demande-conge/',
        'category': 'RH',
    },
]


def index_documents(request):
    """Page Documents : catalogue professionnel avec exemplaire par type."""
    modeles = DocumentModele.objects.filter(est_actif=True)

    context = {
        'catalog': DOCUMENTS_CATALOG,
        'modeles_rh': modeles.filter(categorie='RH'),
        'modeles_admin': modeles.filter(categorie='ADMINISTRATIF'),
        'modeles_pedagogy': modeles.filter(categorie='PEDAGOGIQUE'),
    }
    return render(request, 'documents/documents_list.html', context)


@login_required
def document_sample_pdf(request, key):
    """Exemplaire PDF fictif pour chaque type de document du catalogue."""
    doc = next((d for d in DOCUMENTS_CATALOG if d['key'] == key), None)
    if doc is None:
        messages.error(request, "Type de document inconnu.")
        return redirect('documents:index')

    school = None
    from school_settings.models import SchoolSetting
    try:
        school = SchoolSetting.load()
    except Exception:
        school = None

    sample_data = {
        'certificat_scolarite': {
            'intro': ("Le Directeur de l'établissement atteste que l'élève dont "
                      "l'identité suit est régulièrement inscrit pour l'année :"),
            'fields': [
                ('Nom & Prénom', 'ADJOVI Koffi Marc'),
                ('Matricule', 'STD-2026-0125'),
                ('Né(e) le', '12/03/2012 à Cotonou'),
                ('Classe', '6ème A'),
                ('Année scolaire', '2025-2026'),
            ],
            'conclusion': "En foi de quoi, le présent certificat est délivré à l'intéressé pour servir et valoir ce que de droit.",
        },
        'certificat_frequentation': {
            'intro': "Le Directeur atteste que l'élève ci-dessous fréquente régulièrement l'établissement :",
            'fields': [
                ('Nom & Prénom', 'TRAORE Aminata'),
                ('Matricule', 'STD-2026-0087'),
                ('Classe', '5ème B'),
                ('Taux de fréquentation', '94 %'),
                ('Année scolaire', '2025-2026'),
            ],
            'conclusion': "Le présent certificat est délivré pour faire valoir ce que de droit.",
        },
        'certificat_transfert': {
            'intro': "Le Directeur atteste que l'élève ci-dessous a quitté l'établissement pour transfert :",
            'fields': [
                ('Nom & Prénom', 'KEITA Ibrahim'),
                ('Matricule', 'STD-2025-0042'),
                ('Dernière classe fréquentée', '4ème A'),
                ('École d’accueil', 'Groupe Scolaire La Réussite'),
                ('Motif', 'Déménagement de la famille'),
            ],
            'conclusion': "Son dossier scolaire sera transmis sur simple demande de l'établissement d'accueil.",
        },
        'attestation_reussite': {
            'intro': "Le Directeur atteste que l'élève ci-dessous a réussi sa classe avec honneur :",
            'fields': [
                ('Nom & Prénom', 'SANOGO Rokia'),
                ('Matricule', 'STD-2026-0033'),
                ('Classe validée', 'Terminale C'),
                ('Moyenne annuelle', '14,75 / 20'),
                ('Décision du conseil', 'Admise'),
            ],
            'conclusion': "Félicitations du Conseil de Discipline pour la conduite exemplaire de l'élève.",
        },
        'tableau_honneur': {
            'intro': "Le tableau d'honneur du trimestre récompense les élèves suivants :",
            'fields': [
                ('Élève', 'COULIBALY Mariam — 1ère A'),
                ('Moyenne du trimestre', '17,25 / 20'),
                ('Rang', '1er / 32'),
                ('Mention', 'Très Bien'),
                ('Trimestre', '1er Trimestre — 2025-2026'),
            ],
            'conclusion': "L'établissement félicite chaleureusement l'élève et encourage les efforts de tous.",
        },
        'convocation_parent': {
            'intro': "Madame, Monsieur, vous êtes prié(e) de vous présenter au secrétariat de l'établissement :",
            'fields': [
                ('Élève concerné(e)', 'FALL Cheikh — 3ème B'),
                ('Objet', 'Comportement en classe'),
                ('Date de convocation', 'Jeudi 15 octobre 2026 à 10h00'),
                ('Personne à voir', 'Le Proviseur adjoint'),
                ('Lieu', 'Bureau de la Direction'),
            ],
            'conclusion': "Votre présence est indispensable au bon suivi de la scolarité de votre enfant.",
        },
        'recu_paiement': {
            'intro': "Reçu officiel de paiement des frais de scolarité :",
            'fields': [
                ('N° de reçu', 'REC-2026-0158'),
                ('Payeur', 'M. DIALLO (parent de Awa DIALLO, 6ème A)'),
                ('Montant réglé', '75 000 FCFA'),
                ('Mode de paiement', 'Orange Money'),
                ('Date', '05/10/2026'),
            ],
            'conclusion': "Ce reçu tient lieu de justificatif officiel de règlement. Merci de votre confiance.",
        },
        'bulletin': {
            'intro': "Extrait du bulletin de notes de la période :",
            'fields': [
                ('Élève', 'BARRY Aïssata — 5ème A'),
                ('Moyenne générale', '13,50 / 20'),
                ('Rang', '5 / 28'),
                ('Mention', 'Assez Bien'),
                ('Période', '1er Trimestre — 2025-2026'),
            ],
            'conclusion': "Bulletin complet disponible depuis le menu Bulletins de l'application.",
        },
        'demande_conge': {
            'intro': "Demande de congé adressée à la Direction de l'établissement :",
            'fields': [
                ('Demandeur', 'M. MAIGA Oumar — Enseignant'),
                ('Type de congé', 'Congé annuel'),
                ('Du', '20/12/2026'),
                ('Au', '04/01/2027'),
                ('Motif', 'Congés familiaux'),
            ],
            'conclusion': "Signé le demandeur, avis du supérieur hiérarchique et décision de la Direction.",
        },
    }.get(key, {
        'intro': "Exemplaire de démonstration du document.",
        'fields': [('Document', doc['title'])],
        'conclusion': "Ceci est un exemplaire fictif généré à titre d'illustration.",
    })

    context = {
        'doc': doc,
        'school': school,
        'intro': sample_data['intro'],
        'fields': sample_data['fields'],
        'conclusion': sample_data['conclusion'],
        'reference': f"EX-2026/{doc['key'][:8].upper()}-0001",
        'date_str': timezone.localdate().strftime('%d/%m/%Y'),
    }

    html = render_to_string('documents/sample_pdf.html', context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result, encoding='UTF-8')
    if pdf.err:
        return HttpResponse("Erreur lors de la génération de l'exemplaire.", status=500)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Exemple_{key}.pdf"'
    return response


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