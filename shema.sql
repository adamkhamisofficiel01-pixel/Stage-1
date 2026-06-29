-- =====================================================================
--  ONDA Essaouira Mogador — Schéma Supabase (PostgreSQL)
--
--  À exécuter dans : Supabase Dashboard > SQL Editor > New query
--
--  IMPORTANT — Sécurité :
--  Toutes les requêtes de l'application Flask utilisent la clé
--  SERVICE ROLE (cf. app/database.py -> get_service_db), qui contourne
--  Row Level Security. Flask est donc la SEULE couche d'autorisation
--  (sessions Flask-Login + décorateurs @admin_required /
--  @privilege_required). RLS est activé ci-dessous sans aucune policy,
--  ce qui bloque par défaut tout accès via les clés "anon" / "authenticated"
--  exposées côté navigateur — uniquement la clé service_role (gardée
--  côté serveur, jamais dans le frontend) peut lire/écrire ces tables.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------
create extension if not exists "pgcrypto";


-- ---------------------------------------------------------------------
-- Table: users
-- ---------------------------------------------------------------------
create table if not exists public.users (
    id              uuid primary key default gen_random_uuid(),
    pseudo          text not null unique,
    mail            text,
    fonction        text,
    service         text,
    password_hash   text not null,
    role            text not null default 'user' check (role in ('user', 'admin')),
    privileges      text[] not null default '{}',
    created_at      timestamptz not null default now()
);

comment on table public.users is 'Comptes internes ONDA Essaouira (auth gérée par Flask, pas par Supabase Auth)';
comment on column public.users.privileges is 'Sous-ensemble de: download, add, delete, accessall';

alter table public.users enable row level security;


-- ---------------------------------------------------------------------
-- Table: documents
-- ---------------------------------------------------------------------
create table if not exists public.documents (
    id              uuid primary key default gen_random_uuid(),
    code            text,
    titre           text not null,
    pilote          text,
    date            date,
    type_doc        text not null default 'numerique' check (type_doc in ('numerique', 'papier')),
    fournisseur     text,
    destinataire    text,                 -- nom du service, ou 'public'
    classement      text,                 -- lieu de classement physique
    file_path       text,                 -- chemin dans le bucket Storage "documents"
    file_type       text default 'pdf' check (file_type in ('pdf', 'doc', 'xls', 'ppt')),
    created_by      uuid references public.users(id) on delete set null,
    created_at      timestamptz not null default now()
);

create index if not exists documents_destinataire_idx on public.documents (destinataire);
create index if not exists documents_date_idx on public.documents (date desc);

alter table public.documents enable row level security;


-- ---------------------------------------------------------------------
-- Table: messages (messagerie interne)
-- ---------------------------------------------------------------------
create table if not exists public.messages (
    id              uuid primary key default gen_random_uuid(),
    sender_id       uuid not null references public.users(id) on delete cascade,
    receiver_id     uuid not null references public.users(id) on delete cascade,
    content         text not null,
    is_read         boolean not null default false,
    created_at      timestamptz not null default now()
);

create index if not exists messages_conversation_idx
    on public.messages (sender_id, receiver_id, created_at);
create index if not exists messages_receiver_unread_idx
    on public.messages (receiver_id, is_read);

alter table public.messages enable row level security;


-- =====================================================================
-- Storage: bucket pour les fichiers de documents
-- =====================================================================
-- Le bucket est privé : l'accès aux fichiers passe uniquement par des
-- URLs signées générées côté serveur (create_signed_url), après
-- vérification des privilèges Flask.
insert into storage.buckets (id, name, public)
values ('documents', 'documents', false)
on conflict (id) do nothing;


-- =====================================================================
-- Données de démonstration (seed)
-- =====================================================================
-- Mots de passe en clair pour les comptes de démo (hachés ci-dessous
-- avec werkzeug.security.generate_password_hash, format scrypt) :
--   TIJANI TARIK   (admin)            -> admin123
--   BENALI YOUSSEF (user)             -> user123
--   HADDAD SARA    (user)             -> user123
--   OUALI MEHDI    (user)             -> user123
--
-- Pensez à changer ces mots de passe (ou supprimer ces comptes de
-- démo) avant toute mise en production.

insert into public.users (pseudo, mail, fonction, service, password_hash, role, privileges)
values
    ('TIJANI TARIK', 'tarik.tijani@onda.ma', 'Directeur de l''Aéroport', 'Direction',
        'scrypt:32768:8:1$TYfMPAxCxkC0qX75$0f1d956147418eb39b9f0593082db72403275178d81b2f77bd7f491f3f7d97f4c81221113e7898be5c193947e420e2bab78c5dcea53e9da5d9d485427ba982c8',
        'admin', array['download','add','delete','accessall']),

    ('BENALI YOUSSEF', 'y.benali@onda.ma', 'Contrôleur Aérien', 'Service navigation - control aérien',
        'scrypt:32768:8:1$Mba4i0zIqH22kkp9$e52e76af4f5867a19b1c846de67e79fbf7236a51d212b3ee1b14345e8fb6b8582f253e41e0eb4ce5d73489833cca5af3a42c318f18eb880eb066be09dbc7b258',
        'user', array['download']),

    ('HADDAD SARA', 's.haddad@onda.ma', 'Technicienne CNS', 'Service Technique navigation - CNS',
        'scrypt:32768:8:1$FQk564KPETkv7BK1$33cd2124f9d5e698764f722bbf3fcdfe090e38a047eb37fcb264871e1b93e2b6f3fb2bd826177f7c8ca4cf315a2b58b1a45f0c136c8e3b06d87f800b06b1b8c5',
        'user', array['download','accessall']),

    ('OUALI MEHDI', 'm.ouali@onda.ma', 'Responsable SSQE', 'Service SSQE',
        'scrypt:32768:8:1$zYaDA4BTzQUEAP6j$e378ecdfd3795f197ab0cc97fd7b6d88ce8b8d580e9b1e966ce297763251e292757ab132cc59bb6365d289d006f300b7a7b261227f5df40132f639edd81117d8',
        'user', array['download','add'])
on conflict (pseudo) do nothing;


-- Documents de démonstration (sans fichier joint — file_path NULL)
insert into public.documents (code, titre, pilote, date, type_doc, fournisseur, destinataire, classement, file_type)
values
    ('DOC-001', 'Manuel d''Exploitation Aéroportuaire', 'P0R44', '2024-01-15', 'numerique', 'Direction', 'public', 'Armoire A – Dossier 1', 'pdf'),
    ('DOC-002', 'Procédures de Contrôle Aérien', 'P0R12', '2024-02-10', 'numerique', 'Chef CNS', 'Service navigation - control aérien', 'Armoire B – Dossier 2', 'doc'),
    ('DOC-003', 'Plan de Sécurité Annuel 2024', 'P0R28', '2024-03-01', 'papier', 'Chef SSQE', 'Service SSQE', 'Armoire C – Dossier 3', 'pdf'),
    ('DOC-004', 'Rapport Maintenance CNS Q1', 'P0R55', '2024-04-05', 'numerique', 'Chef technique', 'Service Technique navigation - CNS', 'Armoire A – Dossier 4', 'xls'),
    ('DOC-005', 'Guide des Compagnies Aériennes', 'P0R44', '2024-05-20', 'numerique', 'Direction', 'public', 'Armoire D – Dossier 1', 'ppt')
on conflict do nothing;
