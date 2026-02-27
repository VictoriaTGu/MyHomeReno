# Heroku Deployment Guide for DIY Project Planner

## Overview

This guide explains how to deploy both frontend and backend as a unified project to Heroku with PostgreSQL integration.

**Architecture:**
- Single Git repository with `/mybackend` and `/myfrontend` subdirectories
- React frontend built into static files and served by Django
- Django + Gunicorn runs as single web dyno
- PostgreSQL database managed by Heroku addon

---

## Prerequisites

1. **Heroku CLI** installed: `brew install heroku`
2. **Heroku account** created at heroku.com
3. **Git** repository initialized in project root
4. Logged into Heroku: `heroku login`

---

## Step 1: Create Root-Level Configuration Files

### 1.1 Root `requirements.txt`

**Location:** `/Users/lunayou/Documents/MyHomeReno/requirements.txt`

**Purpose:** Heroku's Python buildpack looks for `requirements.txt` in the root directory. This file installs Python dependencies for the entire project.

**Content:**
```
Django==4.2.0
djangorestframework==3.14.0
gunicorn==20.1.0
whitenoise==6.4.0
dj-database-url==1.3.0
psycopg2-binary==2.9.6
python-decouple==3.8
django-heroku==0.3.1
python-dotenv==1.0.0
langchain==0.0.280
openai==0.27.8
chromadb==0.3.21
```

**How it works:**
- Heroku runs `pip install -r requirements.txt` in root directory
- This installs all backend dependencies globally on the dyno
- The Python buildpack detects this file and activates

---

### 1.2 Root `Procfile`

**Location:** `/Users/lunayou/Documents/MyHomeReno/Procfile`

**Purpose:** Tells Heroku how to start your application.

**Content:**
```
web: cd mybackend && gunicorn mybackend.wsgi --log-file -
release: cd mybackend && python manage.py migrate
```

**How it works:**
- `web:` command starts the web dyno that handles HTTP requests
  - Changes to `mybackend/` directory
  - Starts Gunicorn with Django's WSGI application
  - `--log-file -` streams logs to stdout for `heroku logs`
- `release:` command runs database migrations automatically on every deploy
  - Runs before the web dyno starts
  - Ensures schema is up-to-date

---

### 1.3 Root `runtime.txt`

**Location:** `/Users/lunayou/Documents/MyHomeReno/runtime.txt`

**Purpose:** Specifies Python version to ensure consistency.

**Content:**
```
python-3.11.0
```

**How it works:**
- Heroku's Python buildpack reads this and uses specified version
- Prevents "works on my machine" issues with Python version mismatches

---

### 1.4 Root `.slugignore`

**Location:** `/Users/lunayou/Documents/MyHomeReno/.slugignore`

**Purpose:** Exclude unnecessary files from deployment (reduces app size, speeds up builds).

**Content:**
```
.git
.gitignore
*.pyc
__pycache__
.DS_Store
.env
.env.local
docs/
myfrontend/node_modules/
myfrontend/.env
myfrontend/dist/
mybackend/__pycache__/
mybackend/*/__pycache__/
```

**How it works:**
- Files listed are not deployed to Heroku (smaller "slug")
- Faster deploy, less storage used
- Note: `myfrontend/node_modules/` is excluded because Node.js buildpack reinstalls it anyway

---

### 1.5 Root `heroku.yml`

**Location:** `/Users/lunayou/Documents/MyHomeReno/heroku.yml`

**Purpose:** Defines buildpack order and build process (optional, but recommended for clarity).

**Content:**
```yaml
build:
  languages:
    - python
    - nodejs

run:
  web: cd mybackend && gunicorn mybackend.wsgi --log-file -
  release: cd mybackend && python manage.py migrate
```

**How it works:**
- Explicitly declares buildpacks in order
- Python buildpack: installs Python deps, detects `requirements.txt`
- Node.js buildpack: detects `myfrontend/package.json`, builds React
- `run` section mirrors Procfile commands

---

## Step 2: Update Django Settings

**File:** [mybackend/mybackend/settings.py](../mybackend/mybackend/settings.py)

### Key Production Settings

```python
# ============= DEBUG & SECURITY =============
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
if 'herokuapp.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('*.herokuapp.com')
```

**Purpose:** 
- In production, `DEBUG=False` prevents showing sensitive info in error pages
- `ALLOWED_HOSTS` restricts which domains can access your app
- `*.herokuapp.com` allows your Heroku domain

```python
# ============= DATABASE =============
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

**Purpose:**
- `dj_database_url.config()` parses Heroku's `DATABASE_URL` environment variable
- Heroku automatically sets `DATABASE_URL` when you add PostgreSQL addon
- Format: `postgres://user:password@host:port/database`
- `conn_max_age=600`: Connection pooling (reuse connections for 10 minutes)
- `conn_health_checks=True`: Detects stale connections and reconnects
- Local dev uses SQLite (no DATABASE_URL env var)

```python
# ============= STATIC FILES =============
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'frontend_build',  # Built React files
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**Purpose:**
- `STATIC_URL`: Browser path for accessing static files (`/static/...`)
- `STATIC_ROOT`: Directory where `collectstatic` puts all static files
- `STATICFILES_DIRS`: Include built React frontend in static files
- `WhiteNoiseStorage`: Compresses and enables far-future expires headers for static files (better caching)

```python
# ============= MIDDLEWARE =============
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]
```

**Purpose:**
- Order matters—`WhiteNoiseMiddleware` must come early
- Intercepts requests for `/static/...` and serves efficiently
- Avoids needing a separate static file server (nginx)

```python
# ============= CORS & SECURITY =============
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if os.environ.get('CSRF_TRUSTED_ORIGINS') else []

SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
```

**Purpose:**
- `CSRF_TRUSTED_ORIGINS`: Allows CSRF tokens from your Heroku domain
- `SECURE_SSL_REDIRECT`: Redirects HTTP → HTTPS in production
- `*_SECURE`: Only send cookies over HTTPS (prevents man-in-the-middle)

```python
# ============= HEROKU CONFIGURATION =============
django_heroku.settings(locals())
```

**Purpose:**
- Final line calls `django_heroku` to auto-configure remaining settings
- Sets `SECURE_SSL_REDIRECT`, `ALLOWED_HOSTS`, database config, etc.
- Idiomatic Heroku Django setup

---

## Step 3: Frontend Build Configuration

**File:** [myfrontend/vite.config.js](../myfrontend/vite.config.js)

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../mybackend/frontend_build',
    emptyOutDir: true,
  },
})
```

**How it works:**
- `outDir: '../mybackend/frontend_build'`: Builds React into a directory Django can find
- `emptyOutDir: true`: Removes old builds before creating new ones
- This output is included in Django's `STATICFILES_DIRS`

**File:** [myfrontend/.env.production](../myfrontend/.env.production)

```
VITE_API_BASE_URL=https://<your-app-name>.herokuapp.com/api
```

**How it works:**
- When React is built for production, it uses this API base URL
- All `fetch()` calls to `/api/...` point to your backend
- Replace `<your-app-name>` with your actual Heroku app name

---

## Step 4: Build Process Explained

### What Happens During Deploy

When you run `git push heroku main`:

1. **Git Push:** Code is sent to Heroku's Git server
2. **Buildpack Detection:**
   - Looks for `requirements.txt` → detects Python buildpack
   - Looks for `package.json` → detects Node.js buildpack
3. **Python Buildpack Runs:**
   - Reads `runtime.txt` and installs Python 3.11.0
   - Installs all packages from root `requirements.txt`
4. **Node.js Buildpack Runs:**
   - Installs Node.js
   - Runs `npm install` in `myfrontend/`
   - Runs `npm run build` (or `vite build`)
   - Output goes to `myfrontend/dist/` (but Vite config redirects to `mybackend/frontend_build/`)
5. **Procfile Release Command:**
   - `python manage.py migrate` runs automatically
   - Creates/updates database tables
6. **Procfile Web Command:**
   - `cd mybackend && gunicorn mybackend.wsgi` starts
   - Gunicorn loads Django application
7. **Static Files:**
   - Django's `collectstatic` runs automatically (via WhiteNoise)
   - Copies from `STATICFILES_DIRS` (includes built React) to `STATIC_ROOT`
   - WhiteNoise middleware serves these efficiently

---

## Step 5: Deployment Commands

### 5.1 Initialize Git Repository

```bash
cd /Users/lunayou/Documents/MyHomeReno
git init
git add .
git commit -m "Initial commit: DIY Project Planner for Heroku"
```

**What it does:**
- Creates Git repository in project root
- Stages all files
- Creates initial commit
- Heroku deploys from Git history

---

### 5.2 Create Heroku App

```bash
heroku create <your-app-name>
```

**What it does:**
- Creates new Heroku app
- Adds `heroku` remote to Git
- You'll use this remote to push code
- Replace `<your-app-name>` with your chosen name (must be unique across all Heroku)

**Verify:**
```bash
git remote -v
# Should show:
# heroku  https://git.heroku.com/<your-app-name>.git (fetch)
# heroku  https://git.heroku.com/<your-app-name>.git (push)
```

---

### 5.3 Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:hobby-dev --app=<your-app-name>
```

**What it does:**
- Creates a free PostgreSQL database (hobby-dev tier = 10,000 rows max)
- Automatically sets `DATABASE_URL` environment variable
- Django's `dj_database_url.config()` parses this and configures database

**Verify:**
```bash
heroku config --app=<your-app-name>
# Should show DATABASE_URL with postgres://... connection string
```

---

### 5.4 Set Environment Variables (Critical)

```bash
heroku config:set DEBUG=False --app=<your-app-name>
heroku config:set ALLOWED_HOSTS=<your-app-name>.herokuapp.com --app=<your-app-name>
heroku config:set CSRF_TRUSTED_ORIGINS=https://<your-app-name>.herokuapp.com --app=<your-app-name>
```

**What each does:**
- `DEBUG=False`: Disables debug mode in production
- `ALLOWED_HOSTS`: Only accept requests from your domain
- `CSRF_TRUSTED_ORIGINS`: Allows CSRF tokens from your domain

**For Phase 2/3 features:**
```bash
heroku config:set OPENAI_API_KEY=<your-openai-key> --app=<your-app-name>
heroku config:set SERPAPI_API_KEY=<your-serpapi-key> --app=<your-app-name>
```

**Verify all vars:**
```bash
heroku config --app=<your-app-name>
```

---

### 5.5 Deploy to Heroku

```bash
git push heroku main
```

**What it does:**
1. Sends code to Heroku's Git server
2. Heroku detects buildpacks and runs build process (see Step 4 above)
3. Runs release command (migrations)
4. Starts web dyno with Gunicorn
5. Your app is live!

**Watch logs during deploy:**
```bash
heroku logs --tail --app=<your-app-name>
```

Press `Ctrl+C` to stop streaming logs.

---

### 5.6 Run Database Migrations

Usually happens automatically via Procfile release command, but you can run manually:

```bash
heroku run python mybackend/manage.py migrate --app=<your-app-name>
```

---

### 5.7 Create Django Superuser (Optional)

```bash
heroku run python mybackend/manage.py createsuperuser --app=<your-app-name>
```

**What it does:**
- Creates admin account for Django admin panel
- Access at `https://<your-app-name>.herokuapp.com/admin`

---

### 5.8 Seed Initial Data (Optional)

```bash
heroku run python mybackend/manage.py seed_data --app=<your-app-name>
```

---

## Step 6: Verification

### Open Your App

```bash
heroku open --app=<your-app-name>
```

Should open `https://<your-app-name>.herokuapp.com` in your browser.

### Check Dyno Status

```bash
heroku ps --app=<your-app-name>
```

Should show:
```
web.1       up for X logs
release.1   completed
```

### View Recent Logs

```bash
heroku logs --num=50 --app=<your-app-name>
```

### Test API

```bash
curl https://<your-app-name>.herokuapp.com/api/projects/
```

Should return JSON (or 401 if auth required).

---

## Troubleshooting

### App crashes on startup

**Check logs for errors:**
```bash
heroku logs --tail --app=<your-app-name>
```

**Common issues:**
- Missing `OPENAI_API_KEY` or other env vars
- Database migrations failed (check release logs)
- Static files not found (check `collectstatic` output)

### Static files not loading (CSS/images blank)

**Manually collect static files:**
```bash
heroku run python mybackend/manage.py collectstatic --no-input --app=<your-app-name>
```

**Verify static files exist:**
```bash
heroku run ls -la mybackend/staticfiles --app=<your-app-name>
```

### CSRF token errors

**Ensure env vars are set:**
```bash
heroku config --app=<your-app-name> | grep CSRF
```

Should show `CSRF_TRUSTED_ORIGINS=https://<your-app-name>.herokuapp.com`

### Build fails with Python buildpack error

**Ensure root-level `requirements.txt` exists:**
```bash
ls requirements.txt
```

If missing, Heroku can't detect Python buildpack.

### API calls return 404

**Check your frontend `.env.production`:**
```bash
cat myfrontend/.env.production
```

Should have:
```
VITE_API_BASE_URL=https://<your-app-name>.herokuapp.com/api
```

**Rebuild frontend:**
```bash
npm run build
git add .
git commit -m "Rebuild frontend"
git push heroku main
```

---

## Updating and Redeploying

After making changes:

```bash
# Commit changes
git add .
git commit -m "Description of changes"

# Deploy to Heroku
git push heroku main

# If you made Django migrations:
heroku run python mybackend/manage.py migrate --app=<your-app-name>

# If you added new Python dependencies:
# 1. Update mybackend/requirements.txt
# 2. Copy to root (manually or via script)
# 3. Commit and push
```

---

## Monitoring and Maintenance

### View logs in real-time
```bash
heroku logs --tail --app=<your-app-name>
```

### Monitor resource usage
```bash
heroku ps --app=<your-app-name>
```

### Check for dyno restarts
```bash
heroku logs --app=<your-app-name> | grep "Restarting"
```

### Scale dynos (upgrade tier)
```bash
# View current dyno type
heroku ps --app=<your-app-name>

# Upgrade to higher tier
heroku dyno:type standard-1x --app=<your-app-name>  # Paid only
```

### Database backups
```bash
heroku pg:backups:capture --app=<your-app-name>
heroku pg:backups --app=<your-app-name>
```

---

## Environment Variables Summary

| Variable | Value | Purpose |
|----------|-------|---------|
| `DEBUG` | `False` | Disable debug mode in production |
| `ALLOWED_HOSTS` | `<app-name>.herokuapp.com` | Accept requests from Heroku domain |
| `CSRF_TRUSTED_ORIGINS` | `https://<app-name>.herokuapp.com` | Allow CSRF from frontend |
| `DATABASE_URL` | Auto-set by Heroku | PostgreSQL connection string |
| `OPENAI_API_KEY` | Your key | Phase 3 RAG featuresure |
| `SERPAPI_API_KEY` | Your key | Phase 2 store search |

---

## Buildpack Flow Diagram

```
Git Push
   ↓
Heroku Slug Compiler
   ├─→ Python Buildpack
   │   ├─ Read runtime.txt (python-3.11.0)
   │   ├─ Find requirements.txt (root)
   │   └─ pip install -r requirements.txt
   │
   └─→ Node.js Buildpack
       ├─ Find package.json (myfrontend)
       ├─ npm install
       └─ npm run build (Vite) → outputs to mybackend/frontend_build
          ↓
   Release Phase
   ├─ python manage.py migrate
   └─ python manage.py collectstatic (WhiteNoise auto-runs)
      ├─ Copy from frontend_build/ to staticfiles/
      ├─ Compress files
      └─ Generate manifest
         ↓
   Web Dyno Starts
   └─ gunicorn mybackend.wsgi
      ├─ Loads Django
      ├─ WhiteNoise serves static files
      └─ DRF endpoints handle API requests
```

---

## Additional Resources

- [Heroku Python Documentation](https://devcenter.heroku.com/articles/python-support)
- [Heroku Node.js Documentation](https://devcenter.heroku.com/articles/nodejs-support)
- [Heroku PostgreSQL Documentation](https://devcenter.heroku.com/articles/heroku-postgresql)
- [WhiteNoise for Django](http://whitenoise.evans.io/)
- [Procfile Format](https://devcenter.heroku.com/articles/procfile)
