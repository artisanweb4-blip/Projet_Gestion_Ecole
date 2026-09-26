# PROJET : Système de Gestion d'École (School Management System)

## Contexte
Vous êtes un architecte full-stack senior. Vous devez développer un système de gestion d'école complet (SMS) en utilisant une architecture monolithique avec **Django** et **PostgreSQL**. L'application doit être prête pour la production, modulaire et facilement déployable.

## Stack Technique
| Composant          | Technologie / Outil                                          |
|--------------------|--------------------------------------------------------------|
| **Backend**        | Django 5.x (CBV, ORM optimisé)                               |
| **Base de données**| PostgreSQL (configuration standard dans `settings.py`)       |
| **API**            | Django REST Framework (DRF) – endpoints RESTful              |
| **Authentification**| Modèle `User` personnalisé, rôles (Admin, Enseignant, Étudiant, Parent), JWT |
| **Documentation API** | OpenAPI / ReDoc                                           |
| **Déploiement**    | Docker + docker-compose (avec PostgreSQL et pgAdmin)         |
| **Variables d'environnement** | `python-dotenv` + fichier `.env`                  |

## Architecture du Projet (modèle "app-per-domain")
app/
├── accounts/ # Utilisateurs, rôles, authentification
├── students/ # Profils et métadonnées des étudiants
├── teachers/ # Profils et métadonnées des enseignants
├── courses/ # Cours, sessions, inscriptions
├── trs/ # Planification (semestres, salles, créneaux)
├── assignments/ # Devoirs, soumissions, notation
├── exams/ # Examens, questions, résultats
├── attendance/ # Gestion des présences
├── finance/ # Paiements, reçus, rapports financiers
├── admissions/ # Gestion des admissions
├── core/ # Utilitaires partagés (mixins, bases de modèles)
├── apis/ # Routeurs API (regroupement des endpoints)
└── django_config/ # Settings, URLs, WSGI, ASGI