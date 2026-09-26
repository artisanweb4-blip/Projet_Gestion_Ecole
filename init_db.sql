-- Script d'initialisation PostgreSQL pour le Système de Gestion d'École (SMS Africa)
-- Création des rôles, base de données et permissions

CREATE USER school_user WITH PASSWORD 'school_password';

CREATE DATABASE school_db OWNER school_user;

GRANT ALL PRIVILEGES ON DATABASE school_db TO school_user;

-- Extensions PostgreSQL
\c school_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
