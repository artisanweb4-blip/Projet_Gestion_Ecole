from django import forms
from .models import DocumentModele, DemandeConge

class CertificatScolariteForm(forms.Form):
    """
    Formulaire pour choisir l'élève à qui générer le certificat
    """
    # Remplacez 'eleve_id' par un ModelChoiceField si vous avez un modèle Eleve
    eleve_nom = forms.CharField(label="Nom de l'élève", max_length=100)
    eleve_prenom = forms.CharField(label="Prénom de l'élève", max_length=100)
    matricule = forms.CharField(label="Matricule", max_length=50)
    date_naissance = forms.DateField(label="Date de naissance", widget=forms.DateInput(attrs={'type': 'date'}))
    classe = forms.CharField(label="Classe", max_length=50)
    annee_scolaire = forms.CharField(label="Année scolaire", max_length=20, initial="2025 - 2026")


class DemandeCongeForm(forms.ModelForm):
    """
    Formulaire pour permettre au personnel d'effectuer une demande de congé
    """
    class Meta:
        model = DemandeConge
        fields = ['type_conge', 'date_debut', 'date_fin', 'motif']
        widgets = {
            'type_conge': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Raison de la demande...'}),
        }


class DocumentModeleForm(forms.ModelForm):
    """
    Formulaire pour l'administration pour ajouter un nouveau document
    """
    class Meta:
        model = DocumentModele
        fields = ['titre', 'description', 'categorie', 'type_fichier', 'fichier']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'type_fichier': forms.Select(attrs={'class': 'form-select'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
        }