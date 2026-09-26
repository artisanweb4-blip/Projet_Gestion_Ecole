# SMS Africa - Système de Gestion d'École (School Management System)

Bienvenue sur le projet **SMS Africa**, un système complet et monolithique de gestion scolaire développé avec **Django 5.x**, **Django REST Framework (DRF)**, **PostgreSQL** et une interface web moderne aux teintes et motifs culturels africains.

---

## 🌍 Aperçu de la Plateforme & Thème Visuel
L'interface utilisateur web (`/`) offre un tableau de bord aux teintes chaleureuses du continent (Terre d'ocre `#D97706`, Vert Émeraude `#059669`, Or Savane `#F59E0B` et Ardoise sombre `#0F172A`), intégrant :
- **Tableaux de bord personnalisés par rôle** : Administrateur, Enseignant, Étudiant et Parent d'élève.
- **Module d'Encaissement Mobile Money** : Intégration visuelle et API pour Orange Money, Wave et MTN Mobile Money.
- **Gestion des bulletins scolaires** : Calcul automatique des moyennes pondérées par coefficient et appréciations.
- **Planification d'emploi du temps** : Grille anti-chevauchement des cours et des salles.
- **Documentation API Swagger & ReDoc interactive** intégrée directement sous `/api/docs/`.

---

## 🛠️ Stack Technique
| composant | Technologie |
|---|---|
| **Backend Framework** | Django 5.x (Architecture app-per-domain) |
| **API REST** | Django REST Framework (DRF) & DRF-Spectacular (OpenAPI 3.0) |
| **Authentification** | Token JWT (`djangorestframework-simplejwt`) |
| **Base de Données** | PostgreSQL 16 (avec repli automatique SQLite en local) |
| **Conteneurisation** | Docker & Docker Compose (Web + DB + pgAdmin 4) |
| **Interface Frontend** | Web Dashboard HTML5/CSS3 Vanilla + JavaScript ES6 |

---

## 📂 Architecture des Modules (`app-per-domain`)
```
Projet_Gestion_Ecole/
├── django_config/        # Paramètres globaux settings.py, urls.py, wsgi/asgi
├── core/                 # TimeStampMixin, permissions granulaires et utilitaires
├── accounts/             # Utilisateurs, rôles (Admin, Prof, Élève, Parent), JWT
├── students/             # Profils étudiants, classes et génération de bulletins
├── teachers/             # Profils enseignants et spécialités
├── courses/              # Cours, crédits, coefficients et inscriptions
├── trs/                  # Emploi du temps, semestres, salles, anti-chevauchement
├── assignments/          # Devoirs à rendre, fichiers joints et soumissions
├── exams/                # Examens (QCM/Texte/Fichier) et relevés de notes [0-20]
├── attendance/           # Prise de présence, justificatifs et export CSV
├── finance/              # Frais, paiements Mobile Money et verrouillage des reçus
├── admissions/           # Demandes d'admission d'élèves
├── apis/                 # Routeur API master (/api/v1/)
└── templates/            # Dashboard web au thème Afrique (index.html)
```

---

## 🚀 Déploiement et Lancement Rapid

### Option 1 : Lancement avec Docker Compose (Recommandé)
Assurez-vous que Docker est installé sur votre machine, puis exécutez :
```bash
docker-compose up --build
```
Les services seront automatiquement démarrés :
- 🌐 **Application Web & Dashboard** : [http://localhost:8000](http://localhost:8000)
- 📚 **Documentation Swagger UI** : [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- 📖 **Documentation ReDoc** : [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
- 🐘 **pgAdmin 4 (Gestion BDD)** : [http://localhost:5050](http://localhost:5050) *(Email: `admin@ecole.africa` / Pass: `admin`)*

---

### Option 2 : Lancement Local (Sans Docker)
1. **Activer un environnement virtuel Python** :
   ```bash
   python -m venv venv
   # Sur Windows:
   venv\Scripts\activate
   # Sur Linux/macOS:
   source venv/bin/activate
   ```
2. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```
3. **Appliquer les migrations et alimenter la base de données** :
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python seed_data.py
   ```
4. **Démarrer le serveur de développement** :
   ```bash
   python manage.py runserver
   ```

---

## 🔑 Comptes de Démonstration (Créés par `seed_data.py`)

| Rôle | Adresse Email | Mot de Passe |
|---|---|---|
| **Administrateur** | `admin@ecole.africa` | `admin123` |
| **Enseignant** | `ousmane.kane@ecole.africa` | `teacher123` |
| **Étudiant (Awa BAMBA)** | `awa.bamba@ecole.africa` | `student123` |
| **Étudiant (Koffi KOUASSI)** | `koffi.kouassi@ecole.africa` | `student123` |

---

## 📋 Endpoints Clés de l'API REST v1 (`/api/v1/`)

- **POST** `/api/v1/auth/login/` : Connexion et génération du token JWT (Access + Refresh).
- **GET** `/api/v1/students/{id}/bulletin/` : Génération du bulletin complet avec moyenne générale.
- **GET** `/api/v1/schedules/` : Consultation des créneaux de cours sans chevauchement.
- **GET** `/api/v1/records/export-csv/` : Exportation du relevé de présence au format CSV.
- **GET** `/api/v1/payments/reports/` : Rapport financier des encaissements par mode de paiement.

---

## 🛡️ Règles Métier & Sécurité Appliquées
1. **Horaires d'Emploi du Temps** : Validation automatique empêchant une même salle ou un même enseignant d'occuper deux créneaux simultanés.
2. **Notes scolaires** : Strictement bornées entre 0 et 20 (ou total max de l'examen).
3. **Paiements et Reçus** : Impossibilité de supprimer un règlement financier si le reçu officiel a déjà été émis.
4. **Hashage des Mots de Passe** : Hachage PBKDF2 standard Django avec sécurité JWT.
