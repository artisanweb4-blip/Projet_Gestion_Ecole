# Schéma Entité-Association (ER Diagram) - Système de Gestion d'École

Ce document présente l'architecture de la base de données relationnelle PostgreSQL pour la plateforme scolaire.

```mermaid
erDiagram
    USER ||--o| STUDENT_PROFILE : "possède un profil"
    USER ||--o| TEACHER_PROFILE : "possède un profil"
    CLASSROOM ||--o{ STUDENT_PROFILE : "contient"
    CLASSROOM ||--o{ COURSE : "accueille"
    
    TEACHER_PROFILE ||--o{ COURSE : "enseigne"
    STUDENT_PROFILE ||--o{ ENROLLMENT : "s'inscrit"
    COURSE ||--o{ ENROLLMENT : "a pour inscrits"
    
    COURSE ||--o{ SCHEDULE : "planifié"
    CLASSROOM_ROOM ||--o{ SCHEDULE : "héberge"
    TIME_SLOT ||--o{ SCHEDULE : "définit le créneau"
    SEMESTER ||--o{ SCHEDULE : "s'applique pendant"
    
    COURSE ||--o{ ASSIGNMENT : "comporte"
    ASSIGNMENT ||--o{ ASSIGNMENT_SUBMISSION : "reçoit"
    STUDENT_PROFILE ||--o{ ASSIGNMENT_SUBMISSION : "soumet"
    
    COURSE ||--o{ EXAM : "organise"
    EXAM ||--o{ QUESTION : "contient"
    EXAM ||--o{ EXAM_RESULT : "évalue"
    STUDENT_PROFILE ||--o{ EXAM_RESULT : "obtient note"
    
    STUDENT_PROFILE ||--o{ ATTENDANCE_RECORD : "enregistre"
    COURSE ||--o{ ATTENDANCE_RECORD : "concerne"
    ATTENDANCE_RECORD ||--o| ABSENCE_JUSTIFICATION : "justifié par"
    
    CLASSROOM ||--o{ FEE_STRUCTURE : "fixe les frais"
    STUDENT_PROFILE ||--o{ STUDENT_PAYMENT : "effectue paiement"
    FEE_STRUCTURE ||--o{ STUDENT_PAYMENT : "rattaché à"
    
    CLASSROOM ||--o{ ADMISSION_APPLICATION : "cible"
```

## Description des Tables Clés

1. **`accounts_user`** : Modèle d'utilisateur personnalisé supportant les rôles (`ADMIN`, `TEACHER`, `STUDENT`, `PARENT`).
2. **`students_studentprofile`** : Profil des élèves avec matricule unique `student_number`.
3. **`teachers_teacherprofile`** : Profil des enseignants avec matricule `employee_id`.
4. **`trs_schedule`** : Table d'emploi du temps imposant un anti-chevauchement strict par contraintes d'unicité et validation de modèle (`clean()`).
5. **`finance_studentpayment`** : Enregistrement des règlements bancaires / Mobile Money avec protection contre la suppression si le reçu est émis (`is_receipt_issued = True`).
6. **`exams_examresult`** : Notes sur 20 avec calcul de moyennes dans le bulletin.
