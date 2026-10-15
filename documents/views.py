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


# ---------------------------------------------------------------------------
# Données d'exemple fictives par type de document (PDF et Word).
# ---------------------------------------------------------------------------
DOC_SAMPLE_DATA = {
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
    }

DOC_SAMPLE_DEFAULT = {
        'intro': "Exemplaire de démonstration du document.",
        'fields': [('Document', '__DOC_TITLE__')],
        'conclusion': "Ceci est un exemplaire fictif généré à titre d'illustration.",
    }


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

    if key in DOC_SAMPLE_DATA:
        sample_data = DOC_SAMPLE_DATA[key]
    else:
        sample_data = dict(DOC_SAMPLE_DEFAULT)
        sample_data['fields'] = [('Document', doc['title'])]

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
    """Certificat de fréquentation : renvoie l'exemplaire PDF du catalogue."""
    return redirect('documents:document_sample', key='certificat_frequentation')


def generate_certificat_transfert(request):
    """Certificat de transfert : renvoie l'exemplaire PDF du catalogue."""
    return redirect('documents:document_sample', key='certificat_transfert')


def registre_presence(request):
    """Registre de présence : renvoie l'exemplaire PDF du catalogue."""
    return redirect('documents:document_sample', key='registre_presence')


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


# ---------------------------------------------------------------------------
# Génération Word (.docx) : exemple professionnel au format PAYSAGE A4.
# Implémentation en OOXML PUR (zipfile + XML) : AUCUN module externe requis.
# ---------------------------------------------------------------------------
import zipfile as _zipfile

_WORD_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '</Types>'
)

_WORD_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    '</Relationships>'
)

_WORD_DOC_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
)


def _xml_escape(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def _w_run(text, size_half, bold=False, italic=False, color='1E293B'):
    rpr = '<w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>'
    if bold:
        rpr += '<w:b/>'
    if italic:
        rpr += '<w:i/>'
    rpr += '<w:color w:val="%s"/><w:sz w:val="%d"/><w:szCs w:val="%d"/></w:rPr>' % (
        color, size_half, size_half)
    return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, _xml_escape(text))


def _w_p(runs_xml='', jc=None, before=0, after=120, border=None):
    """Paragraphe. border = (couleur, taille_eighth_pt) pour un trait bas."""
    ppr = '<w:pPr>'
    if border:
        ppr += ('<w:pBdr><w:bottom w:val="single" w:sz="%d" w:space="1" w:color="%s"/></w:pBdr>'
                % (border[1], border[0]))
    ppr += '<w:spacing w:before="%d" w:after="%d"/>' % (before, after)
    if jc:
        ppr += '<w:jc w:val="%s"/>' % jc
    ppr += '</w:pPr>'
    return '<w:p>%s%s</w:p>' % (ppr, runs_xml)


def _w_cell(width_twips, paragraphs_xml, fill=None):
    tcpr = '<w:tcPr><w:tcW w:w="%d" w:type="dxa"/>' % width_twips
    if fill:
        tcpr += '<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % fill
    tcpr += ('<w:tcMar><w:top w:w="80" w:type="dxa"/><w:left w:w="120" w:type="dxa"/>'
             '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tcMar></w:tcPr>')
    return '<w:tc>%s%s</w:tc>' % (tcpr, paragraphs_xml)


def _w_table(cols_twips, rows_xml, align='center'):
    edges = ('top', 'left', 'bottom', 'right', 'insideH', 'insideV')
    borders = ''.join(
        '<w:%s w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>' % e for e in edges)
    grid = ''.join('<w:gridCol w:w="%d"/>' % w for w in cols_twips)
    return ('<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="%s"/>'
            '<w:tblBorders>%s</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr>'
            '<w:tblGrid>%s</w:tblGrid>%s</w:tbl>'
            % (sum(cols_twips), align, borders, grid, rows_xml))


@login_required
def document_sample_word(request, key):
    """Exemple du document au format Word (.docx) — paysage A4 professionnel.

    Généré en OOXML pur (stdlib) : fonctionne même sans python-docx installé.
    """
    doc = next((d for d in DOCUMENTS_CATALOG if d['key'] == key), None)
    if doc is None:
        messages.error(request, "Type de document inconnu.")
        return redirect('documents:index')

    from school_settings.models import SchoolSetting
    try:
        school = SchoolSetting.load()
    except Exception:
        school = None
    if key in DOC_SAMPLE_DATA:
        data = DOC_SAMPLE_DATA[key]
    else:
        data = dict(DOC_SAMPLE_DEFAULT)
        data['fields'] = [('Document', doc['title'])]

    school_name = getattr(school, 'school_name', None) or "Gestion d'École"
    school_address = getattr(school, 'address', '') or ''
    school_phone = getattr(school, 'phone', '') or ''
    reference = "EX-2026/%s-0001" % doc['key'][:8].upper()
    ts_str = timezone.localtime().strftime('%d/%m/%Y %H:%M')

    # Largeurs en twips (1 cm = 567 twips) — largeur utile : 26,1 cm = 14 782
    TOTAL_W = 14782
    LEFT_W = 8800                      # école
    RIGHT_W = TOTAL_W - LEFT_W         # titre
    LABEL_W = 4252                     # 7,5 cm
    VALUE_W = TOTAL_W - LABEL_W
    HALF_W = TOTAL_W // 2

    body = []

    # ---- En-tête : école à gauche / titre + référence à droite
    left_cell = _w_cell(LEFT_W,
        _w_p(_w_run(school_name, 32, bold=True, color='1D3557'), after=40)
        + _w_p(_w_run(_fmt_meta(school_address, school_phone), 18, color='64748B'), after=0))
    right_cell = _w_cell(RIGHT_W,
        _w_p(_w_run(doc['title'].upper(), 28, bold=True, color='E63946'), jc='right', after=40)
        + _w_p(_w_run("Réf : %s" % reference, 19, bold=True, color='457B9D'),
               jc='right', after=0))
    body.append(_w_table([LEFT_W, RIGHT_W], '<w:tr>%s%s</w:tr>' % (left_cell, right_cell), align='left'))

    # ---- Trait bleu nuit
    body.append(_w_p(after=200, border=('1D3557', 18)))

    # ---- Introduction
    body.append(_w_p(_w_run(data['intro'], 22, color='1E293B'), after=200))

    # ---- Tableau d'identité (libellé / valeur)
    rows = []
    for label, value in data['fields']:
        rows.append('<w:tr>%s%s</w:tr>' % (
            _w_cell(LABEL_W, _w_p(_w_run(label, 20, bold=True, color='64748B'),
                                  before=40, after=40), fill='F8F9FA'),
            _w_cell(VALUE_W, _w_p(_w_run(value, 20, color='1E293B'), before=40, after=40))))
    body.append(_w_table([LABEL_W, VALUE_W], ''.join(rows)))

    # ---- Conclusion
    body.append(_w_p(_w_run(data['conclusion'], 21, italic=True, color='334155'), before=240, after=120))

    # ---- Signatures : cachet à gauche / Directeur à droite
    sig_left = _w_cell(HALF_W,
        _w_p(_w_run("Cachet de l'établissement", 20, color='334155'), before=480, after=0))
    sig_right = _w_cell(HALF_W,
        _w_p(_w_run("Le Directeur,", 20, color='334155'), jc='right', before=480, after=0)
        + _w_p(_w_run('', 20), jc='right', after=0)
        + _w_p(_w_run('', 20), jc='right', after=0)
        + _w_p(_w_run('', 20), jc='right', after=0)
        + _w_p(_w_run('Nom et signature', 17, color='64748B'), jc='right', after=0))
    body.append(_w_table([HALF_W, HALF_W], '<w:tr>%s%s</w:tr>' % (sig_left, sig_right), align='left'))

    # ---- Pied de page
    body.append(_w_p(
        _w_run("Document généré le %s — %s" % (ts_str, school_name), 16, color='94A3B8'),
        jc='center', before=320, after=0))

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>%s'
        '<w:sectPr>'
        '<w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>'
        '<w:pgMar w:top="851" w:right="1021" w:bottom="851" w:left="1021" '
        'w:header="709" w:footer="709" w:gutter="0"/>'
        '</w:sectPr></w:body></w:document>' % ''.join(body))

    buffer = BytesIO()
    with _zipfile.ZipFile(buffer, 'w', _zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', _WORD_CONTENT_TYPES)
        zf.writestr('_rels/.rels', _WORD_RELS)
        zf.writestr('word/document.xml', document_xml)
        zf.writestr('word/_rels/document.xml.rels', _WORD_DOC_RELS)

    response = HttpResponse(buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = 'attachment; filename="Exemple_%s.docx"' % key
    return response


def _fmt_meta(address, phone):
    if address and phone:
        return "%s · Tél : %s" % (address, phone)
    return address or ("Tél : %s" % phone if phone else '')
