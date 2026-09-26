
**Remarque** : Le `base.html` doit contenir toute la structure HTML fournie (sidebar, main container) avec des blocs Django (`{% block content %}`) pour le contenu principal. Les pages comme `dashboard.html`, `settings.html`, `students/list.html`, etc. hériteront de `base.html` et rempliront le bloc `content`.

---

## MODULES FONCTIONNELS (conformes à l’image et au code HTML)

### 1. Tableau de bord (`dashboard.html`)
- **KPI** : Total élèves, Enseignants, Classes, Taux de présence (statistiques dynamiques)
- **Activités récentes** : Liste des dernières actions (modèle `Activity`)
- **À venir** : Événements planifiés (modèle `Event`)
- **Graphiques** :
  - Performance académique : moyennes par classe (Chart.js)
  - État financier : recettes vs dépenses mensuelles (Chart.js)
- **Totaux financiers** : Recettes, Dépenses, Solde (en FCFA)

### 2. Paramètres (`settings.html`)
- **Onglets** : Général, École, Notifications, Utilisateurs, Sauvegarde, Sécurité
- **Contenu dynamique** :
  - **Général** : Langue, fuseau horaire, année académique active
  - **École** : Nom, slogan, adresse, logo, cachet, devise
  - **Notifications** : Alertes SMS, rappels, etc.
  - **Utilisateurs** : Cartes des rôles (Administrateurs, Enseignants, Parents, Comptables) avec compteurs, et bouton "Gérer les rôles"
  - **Sauvegarde** : Date de dernière sauvegarde, téléchargement
  - **Sécurité** : Politique de mot de passe, expiration des sessions

### 3. Gestion des élèves (`students/`)
- **Fiche élève complète** : photo, QR code, code barre, matricule, état civil, santé, contacts, historique, documents numérisés
- **Liste** : tableau avec colonnes (Matricule, Nom & Prénom, Classe, Statut, Actions)
- **CRUD** : Création, modification, suppression (avec confirmation HTMX)
- **Recherche et filtres**

### 4. Gestion des enseignants (`teachers/`)
- **Profil** : photo, diplômes, spécialité, ancienneté, salaire
- **Liste** : tableau (Nom, Matière, Classes assignées, Statut)
- **CRUD** complet

### 5. Gestion des parents (`parents/`)
- **Compte parent** : lié à User, avec accès restreint
- **Dashboard parent** : suivi de l’enfant (bulletins, paiements, emploi du temps, convocations, notes, absences, discipline)
- **Liste** : tableau (Famille, Élève(s) associé(s), Téléphone, Mode de paiement)

### 6. Gestion des classes (`classes/`)
- **Niveaux** : 1ère à 9ème année (configurable)
- **Sections** : Française, Arabe, Mixte
- **Effectif** (calculé automatiquement)
- **Salle, responsable** (enseignant principal)
- **Liste** : Code Classe, Niveau, Professeur Principal, Effectif

### 7. Matières (`subjects/`)
- Nom, coefficient, programme, horaire, enseignant assigné
- Liste et formulaires

### 8. Programmes scolaires (`programs/`)
- Programme officiel (français, arabe) par année, trimestre, matière
- Structure : chapitres, objectifs, ressources

### 9. Emplois du temps (`schedules/`)
- Génération automatique (algorithme de satisfaction de contraintes) ou manuelle
- Gestion des conflits (enseignant/salle/classe)
- Affichage : planning hebdomadaire (grille)

### 10. Présences (`attendance/`)
- Prise de présence par séance (Présent/Absent/Retard/Excusé) avec HTMX
- Suivi des absences par élève
- Envoi SMS automatique (simulation) aux parents en cas d’absence injustifiée
- Justificatifs (upload, validation)

### 11. Notes (`grades/`)
- **Types** : Devoirs, Interrogations, Compositions, Examens blancs, Examens
- Saisie par matière/classe/trimestre
- Calcul automatique : moyennes, rangs, mentions, statistiques
- Graphiques (évolution des notes)
- Export Excel / PDF

### 12. Bulletins (`report_cards/`)
- Types : Mensuel, Trimestriel, Annuel
- Contenu : notes, moyennes, appréciations, absences, comportement
- Génération PDF avec signature, cachet, QR Code
- Impression et téléchargement

### 13. Documents scolaires (`school_documents/`)
- Attestations (réussite, scolarité, fin d’année), Tableau d’honneur, Certificat, Convocations, Décisions, Sanctions, Reçus, Factures
- Génération PDF

### 14. Comptabilité (`accounting/`)
- **Frais** : Inscription, Réinscription, Scolarité, Transport, Cantine, Uniformes, Activités
- **Paiements** : Espèces, Orange Money, Moov Money, Wave, Chèque, Banque
- Historique, relances, remises, bourses
- Liste des paiements (Reçu #, Payeur, Mode, Montant, Statut)

### 15. Dépenses (`expenses/`)
- Fournisseurs, factures, salaires, charges (électricité, eau, internet, achat, maintenance)
- CRUD

### 16. Rapports (`reports/`)
- Recettes, Dépenses, Balance, Situation d’un élève/classe/enseignant
- Export PDF / Excel

### 17. Communication (`communication/`)
- Notifications in-app, SMS, WhatsApp, Emails, Convocations, Alertes, Annonces

### 18. Sécurité (`security/`)
- Double authentification (2FA) optionnelle
- Journal d’activités
- Sauvegardes automatiques
- Permissions fines

### 19. Utilisateurs (Rôles)
- Administrateur, Directeur, Surveillant général, Secrétaire, Comptable, Enseignant, Parent, Élève, Bibliothécaire

---

## PHASES DE DÉVELOPPEMENT (génération séquentielle)

### PHASE 1 : Configuration initiale
- `requirements.txt`, `docker-compose.yml`, `Dockerfile`, `.env.example`
- `manage.py`, `app/django_config/settings.py` (config PostgreSQL, static, media, auth_user_model)
- Structure des dossiers : `app/static/css/custom.css`, `app/static/js/main.js`, `app/media/`
- `app/django_config/urls.py` (inclure les URLs des apps)

### PHASE 2 : Application "core" (mixins et context processors)
- `TimeStampMixin`, `SoftDeleteMixin`
- Context processor pour injecter les menus dynamiques, le profil utilisateur, les statistiques globales
- Utilitaires : génération QR Code, code barre, matricule

### PHASE 3 : Application "accounts" (authentification)
- `CustomUserManager`, `User` (email, prénom, nom, rôle, phone, is_active, is_staff, is_superuser)
- `LoginView`, `LogoutView`, `RegisterView` (inscription avec choix rôle)
- Templates : `registration/login.html`, `registration/register.html`, `registration/password_reset.html` (intégrés dans base.html)
- JWT pour l’API

### PHASE 4 : Application "dashboard"
- Modèles : `Activity` (titre, auteur, date), `Event` (titre, date)
- Vue : `DashboardView` (redirection selon rôle)
- Template : `dashboard/dashboard.html` (exactement comme le code HTML fourni, avec données dynamiques)
- Context : KPI, activités récentes, événements à venir, données pour les graphiques (Chart.js)

### PHASE 5 : Application "settings" (Paramètres)
- Modèles : `SchoolConfig` (nom, slogan, adresse, logo, cachet, devise, année académique active, etc.), `AcademicYear`, `Trimester`, `Mention`, `GradeScale`
- Vues : `SettingsView` (affichage), `SettingsUpdateView` (sauvegarde)
- Template : `settings/settings.html` (reproduisant l’interface avec les 6 onglets) avec des formulaires pour chaque section

### PHASE 6 : Application "students" (Élèves)
- Modèle `Student` (tous les champs listés : photo, QR, code barre, matricule, état civil, santé, historique, documents)
- Vues : CRUD complet (`ListView`, `CreateView`, `UpdateView`, `DeleteView`, `DetailView`)
- Templates : `students/list.html`, `students/form.html`, `students/detail.html`
- Génération automatique du QR code et code barre à la création

### PHASE 7 : Application "teachers" (Enseignants)
- Modèle `Teacher` (photo, diplômes, spécialité, ancienneté, salaire)
- Vues CRUD + templates

### PHASE 8 : Application "parents" (Parents)
- Modèle `Parent` (lié à User) et `ParentChild` (liaison parent ↔ étudiant)
- Vues : Dashboard parent (suivi enfant), consultation bulletins, paiements, emploi du temps, convocations, notes, absences, discipline
- Templates : `parents/dashboard.html`, `parents/list.html`, `parents/form.html`

### PHASE 9 : Application "classes" (Classes)
- Modèle `Class` (niveau, section, effectif (calculé), salle, responsable)
- Vues CRUD + templates

### PHASE 10 : Application "subjects" et "programs"
- `Subject` (nom, coefficient, horaire, enseignant)
- `Program` (officiel, année, trimestre, matière, chapitres)
- Vues CRUD

### PHASE 11 : Application "schedules" (Emplois du temps)
- Modèles : `Schedule` (classe, enseignant, salle, jour, heure début/fin)
- Vues : liste, génération automatique (algorithme simple), saisie manuelle
- Templates : `schedules/list.html`, `schedules/generate.html`, `schedules/manual.html`

### PHASE 12 : Application "attendance" (Présences)
- Modèles : `AttendanceSession` (classe, date, matière), `AttendanceRecord` (élève, statut)
- Vue : `TakeAttendanceView` (HTMX pour mise à jour en direct)
- Templates : `attendance/take.html`, `attendance/report.html`
- Intégration SMS (simulation)

### PHASE 13 : Application "grades" (Notes)
- Modèles : `Exam` (type, coefficient, date), `Grade` (élève, matière, exam, note)
- Vues : saisie des notes, relevé, statistiques
- Templates : `grades/entry.html`, `grades/report.html`
- Calcul automatique des moyennes, rangs, mentions, export Excel/PDF

### PHASE 14 : Application "report_cards" (Bulletins)
- Modèle : `ReportCard` (élève, trimestre, notes, moyenne, appréciation, absences, comportement)
- Vues : génération PDF (WeasyPrint), liste
- Templates : `report_cards/list.html`, `report_cards/preview.html`
- Intégration signature, cachet, QR Code dans PDF

### PHASE 15 : Application "school_documents" (Documents scolaires)
- Modèles : `DocumentTemplate` (type, contenu), génération des attestations, certificats, convocations, reçus, factures, sanctions
- Vues de génération PDF
- Templates : `school_documents/list.html`, `school_documents/generate.html`

### PHASE 16 : Application "accounting" (Comptabilité)
- Modèles : `Fee` (type, montant, échéance), `Payment` (élève, fee, montant, méthode (Orange Money, Moov Money, Wave, etc.), statut, transaction_id)
- Vues : liste des paiements, création, reçu PDF, relances
- Templates : `accounting/payments.html`, `accounting/receipts.html`

### PHASE 17 : Application "expenses" (Dépenses)
- Modèle `Expense` (fournisseur, montant, catégorie, date, justificatif)
- Vues CRUD

### PHASE 18 : Application "reports" (Rapports)
- Vues : rapports (recettes, dépenses, balance, situations)
- Templates : `reports/dashboard.html`, `reports/exports.html`
- Export PDF/Excel

### PHASE 19 : Application "communication"
- Modèles : `Notification`, `Message`, `Alert`, `Announcement`
- Vues : envoi SMS, email, WhatsApp (simulations)
- Templates : `communication/notifications.html`, `communication/announcements.html`

### PHASE 20 : Application "security"
- Modèles : `ActivityLog`, `Backup`
- Vues : historique, gestion 2FA, sauvegardes
- Templates : `security/history.html`, `security/backups.html`

### PHASE 21 : Génération API REST (DRF)
- Sérializers pour tous les modèles
- ViewSets avec permissions
- Routers, documentation Swagger/ReDoc

---

## RÈGLES TRANSVERSALES (OBLIGATOIRES)

1. **Templates** : Tous les templates héritent de `base.html` (fourni). Le `base.html` contient la sidebar, le header, le footer, les blocs `content` et `extra_js`.
2. **Sidebar dynamique** : Les liens de navigation sont générés par un contexte (`menu_items`) selon le rôle de l’utilisateur.
3. **Données dynamiques** : Les KPI, activités, événements, graphiques, tableaux et paramètres sont peuplés par les vues.
4. **HTMX** : Utiliser pour les actions sans rechargement (suppression, prise de présence, mise à jour de statut).
5. **Formulaires** : Utiliser `django-crispy-forms` avec le pack Bootstrap 5, ou ajouter manuellement les classes CSS.
6. **Fichiers statiques** : CSS et JS personnalisés dans `app/static/`, chargés via `{% static %}`.
7. **Sécurité** : Toutes les vues Web utilisent `LoginRequiredMixin` et `RoleRequiredMixin` (à créer).
8. **PDF** : WeasyPrint (ou ReportLab) pour les documents.
9. **Export Excel** : openpyxl.
10. **Langue** : Interface en français.

---

## LIVRABLES FINAUX
1. Code source complet (toutes les apps, templates, statics).
2. Fichiers de migration.
3. `docker-compose.yml`.
4. Jeu de données initial (`fixtures/initial_data.json`) avec au moins : 1 admin, 1 directeur, 1 enseignant, 1 parent, 1 élève, 1 classe, 1 matière, 1 trimestre, quelques activités/événements.
5. `README.md` (installation, configuration, lancement).
6. Schéma ER de la BDD.
7. Collection Postman pour l’API.

---

## DÉCLENCHEMENT
**Je valide le démarrage. Commence immédiatement par la PHASE 1.**  
À la fin de chaque phase, écris : **"Phase X terminée. En attente de votre instruction pour la phase suivante."** et arrête-toi. Je te dirai "Continuer" quand je serai prêt.

---

**Ce prompt est final et intègre exactement l’interface HTML fournie. Tous les templates seront générés en respectant ce design.**