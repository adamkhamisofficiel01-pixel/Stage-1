# ONDA Essaouira Mogador — Intranet

Application interne (Flask + Supabase) pour l'Aéroport Essaouira Mogador :
authentification, gestion des utilisateurs et privilèges, bibliothèque
documentaire (avec stockage de fichiers) et messagerie interne.

## Stack

- **Backend** : Flask 3, Flask-Login (sessions), Flask-WTF (protection CSRF)
- **Base de données / Stockage** : Supabase (PostgreSQL + Storage)
- **Frontend** : Jinja2, CSS personnalisé, JS vanilla

## Structure du projet

```
Stageproject/
├── app/
│   ├── __init__.py          # App factory, login manager, CSRF, blueprints
│   ├── database.py          # Clients Supabase (anon + service role)
│   ├── decorators.py         # @admin_required, @privilege_required
│   ├── models.py             # Classe User (Flask-Login)
│   ├── auth/                 # Connexion / déconnexion
│   ├── main/                 # Page d'accueil
│   ├── users/                # Gestion des utilisateurs (admin)
│   ├── documents/            # Bibliothèque documentaire
│   ├── chat/                 # Messagerie interne (API JSON)
│   ├── templates/
│   └── static/{css,js,images}
├── shema.sql                 # Schéma Supabase (tables, RLS, seed)
├── requirements.txt
├── .env / .env.example
└── run.py
```

## 1. Configuration Supabase

1. Créez un projet sur [supabase.com](https://supabase.com) (ou utilisez le
   projet déjà configuré dans `.env`).
2. Ouvrez **SQL Editor** et exécutez le contenu de `shema.sql` : il crée les
   tables `users`, `documents`, `messages`, active Row Level Security, crée
   le bucket de stockage `documents` (privé) et insère des données de
   démonstration.
3. Dans **Project Settings > API**, récupérez :
   - `Project URL` → `SUPABASE_URL`
   - `anon` `public` key → `SUPABASE_KEY`
   - `service_role` key → `SUPABASE_SERVICE_KEY` (⚠️ secret, jamais côté client)

## 2. Configuration de l'application

```bash
cp .env.example .env
# puis éditez .env avec vos valeurs Supabase
```

Le fichier `.env` fourni contient déjà des identifiants Supabase de
démonstration — vérifiez simplement qu'ils correspondent à votre projet,
ou remplacez-les par les vôtres.

**Important** : `.env` est ignoré par Git (`.gitignore`). Ne le commitez
jamais et changez `FLASK_SECRET_KEY` en production.

### Configuration de l'envoi d'emails (mot de passe oublié)

La fonctionnalité « mot de passe oublié » envoie un email via SMTP. Renseignez
dans `.env` :

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=votre-adresse@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-application
MAIL_DEFAULT_SENDER=ONDA Essaouira <votre-adresse@gmail.com>
```

> Avec Gmail, `MAIL_PASSWORD` doit être un **mot de passe d'application**
> (Compte Google → Sécurité → Mots de passe des applications), pas votre
> mot de passe Gmail habituel — Google bloque les connexions SMTP avec le
> mot de passe normal par défaut.

Tant que ces variables ne sont pas configurées, le formulaire « Mot de passe
oublié » reste accessible mais l'envoi de l'email échouera (message
d'erreur générique affiché à l'utilisateur, détail de l'erreur à consulter
dans les logs du serveur).

## 3. Installation

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Lancer l'application

```bash
# Développement
export FLASK_ENV=development        # Windows : set FLASK_ENV=development
python run.py
```

L'application est accessible sur **http://localhost:5000**.

En production, utilisez gunicorn :

```bash
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

## Comptes de démonstration

| Pseudo          | Mot de passe | Rôle  | Privilèges                          |
|-----------------|--------------|-------|--------------------------------------|
| TIJANI TARIK    | admin123     | admin | download, add, delete, accessall     |
| BENALI YOUSSEF  | user123      | user  | download                              |
| HADDAD SARA     | user123      | user  | download, accessall                   |
| OUALI MEHDI     | user123      | user  | download, add                         |

> ⚠️ Changez ou supprimez ces comptes avant toute mise en production.

## Privilèges

- **`download`** : télécharger les fichiers joints aux documents
- **`add`** : ajouter de nouveaux documents
- **`delete`** : supprimer des documents (bouton visible sur chaque carte
  document et dans la fenêtre de détail, avec confirmation)
- **`accessall`** : voir tous les documents, quel que soit le service
  destinataire
- **Rôle `admin`** : accès complet, y compris la gestion des utilisateurs
  (`/users`)

## Visibilité des documents

Un document est visible par un utilisateur si :
- il est administrateur, ou possède le privilège `accessall`, **ou**
- le champ `destinataire` du document correspond à son `service`, **ou**
- le champ `destinataire` est `public`.

## Mot de passe oublié

Sur la page de connexion, le lien « Mot de passe oublié ? » mène à
`/forgot-password` :
1. L'utilisateur saisit son **pseudo ou son email**.
2. S'il existe un compte correspondant avec une adresse email enregistrée,
   un email est envoyé avec un lien de réinitialisation **valable 1 heure**.
3. Le même message de confirmation s'affiche que le compte existe ou non
   (pas d'énumération de comptes).
4. Le lien mène à `/reset-password/<token>` où l'utilisateur choisit un
   nouveau mot de passe (6 caractères minimum).

Le token est généré et vérifié avec `itsdangerous` (signature + expiration),
sans nécessiter de table dédiée en base de données.

## Documents récents cliquables (page d'accueil)

Le panneau « Derniers documents » de la page d'accueil est cliquable : un
clic sur une ligne ouvre la même fenêtre de détail que sur la page
Documents (métadonnées + bouton de téléchargement si le privilège
`download` est présent).

## Sécurité

- Mots de passe hachés avec `werkzeug.security` (scrypt).
- Toutes les routes protégées par `@login_required` ; `/users` également par
  `@admin_required` ; les actions sur les documents par `@privilege_required`.
- Protection CSRF (Flask-WTF) sur tous les formulaires et l'API chat.
- Les fichiers de documents sont stockés dans un bucket Supabase **privé** ;
  le téléchargement passe par une URL signée à durée limitée (60s), générée
  uniquement si l'utilisateur a le privilège `download` et la visibilité sur
  le document.
- Row Level Security est activé sur toutes les tables sans policy : seule la
  clé `service_role` (utilisée côté serveur par Flask, jamais exposée au
  navigateur) peut y accéder. Flask est la couche d'autorisation.
- Les tokens de réinitialisation de mot de passe sont signés et expirent
  après 1 heure ; ils ne sont jamais stockés en base de données.

## Notes

- La messagerie interne utilise un système de *polling* (rafraîchissement
  toutes les 4 secondes) plutôt que Supabase Realtime, pour rester simple
  côté serveur Flask classique (WSGI).
- Le slideshow de la page d'accueil et les infos techniques de l'aéroport
  sont des contenus statiques côté frontend.
