# Heroku Deployment - Quick Start Summary

## Problem Fixed

**Error:** `Your app is configured to use the Python buildpack, but we couldn't find any supported Python project files.`

**Root Cause:** Heroku's Python buildpack was looking for `requirements.txt` in the root directory, but your dependencies were only in `mybackend/requirements.txt`.

**Solution:** Created root-level `requirements.txt` that contains all backend dependencies. Heroku now finds it and activates the Python buildpack.

---

## Files Created/Updated

### 1. `/requirements.txt` (ROOT)
- Contains all Python dependencies
- Heroku's Python buildpack installs these globally
- Includes: Django, DRF, Gunicorn, WhiteNoise, dj-database-url, etc.

### 2. `/Procfile` (ROOT)
```
web: cd mybackend && gunicorn mybackend.wsgi --log-file -
release: cd mybackend && python manage.py migrate
```
- `web` process: Starts Gunicorn to serve your app
- `release` process: Runs migrations automatically before web starts

### 3. `/runtime.txt`
```
python-3.12.1
```
- Specifies Python version for consistency

### 4. `/.slugignore`
- Excludes unnecessary files from deployment
- Reduces app size and deploy time

### 5. `/heroku.yml`
- Explicitly declares buildpack order
- Tells Heroku to use both Python and Node.js buildpacks

### 6. `/myfrontend/.env.production`
```
VITE_API_BASE_URL=https://my-home-reno.herokuapp.com/api
```
- Points React frontend to your backend API on Heroku

### 7. `/myfrontend/vite.config.js` (Already configured)
```javascript
build: {
  outDir: '../mybackend/frontend_build',
  emptyOutDir: true,
}
```
- Builds React into `mybackend/frontend_build/`
- Django serves these files as static content

---

## Deployment Steps

### Step 1: Ensure Git is set up
```bash
cd /Users/lunayou/Documents/MyHomeReno
git status
# Should show your files committed
```

### Step 2: Create Heroku app
```bash
heroku create my-home-reno
# Or if app already exists:
heroku git:remote -a my-home-reno
```

### Step 3: Add PostgreSQL database
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

### Step 4: Set environment variables
```bash
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=my-home-reno.herokuapp.com
heroku config:set CSRF_TRUSTED_ORIGINS=https://my-home-reno.herokuapp.com
heroku config:set OPENAI_API_KEY=<your-key>
heroku config:set SERPAPI_API_KEY=<your-key>
```

### Step 5: Deploy
```bash
git push heroku master
# (or main, depending on your default branch)
```

Watch the logs:
```bash
heroku logs --tail
```

### Step 6: Run migrations
```bash
heroku run python mybackend/manage.py migrate
```

### Step 7: Create superuser (optional)
```bash
heroku run python mybackend/manage.py createsuperuser
```

### Step 8: Verify
```bash
heroku open
# Opens https://my-home-reno.herokuapp.com
```

---

## How the Build Process Works

1. **Git Push** → Code sent to Heroku
2. **Buildpack Detection:**
   - `requirements.txt` found → Python buildpack activated
   - `package.json` (in myfrontend) found → Node.js buildpack activated
3. **Python Buildpack:**
   - Installs Python 3.12.1
   - Runs `pip install -r requirements.txt`
4. **Node.js Buildpack:**
   - Installs Node.js
   - Runs `npm install` in `myfrontend/`
   - Runs `npm run build` → builds React
   - Output goes to `myfrontend/dist/` (but Vite redirects to `mybackend/frontend_build/`)
5. **Release Phase:**
   - Runs `python manage.py migrate`
6. **Web Dyno Starts:**
   - Runs `cd mybackend && gunicorn mybackend.wsgi`
   - Django serves both API and static frontend files
   - WhiteNoise middleware serves React build efficiently

---

## Database Connection

Heroku **automatically sets** `DATABASE_URL` environment variable when you add PostgreSQL addon.

Your Django settings parse this:
```python
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
```

This connects Django to Heroku's PostgreSQL database automatically.

---

## Static Files Flow

1. **Frontend build** → React outputs to `mybackend/frontend_build/`
2. **Django collectstatic** → Copies all static files to `mybackend/staticfiles/`
   - Includes frontend build files
   - Compresses with WhiteNoise
3. **Browser request** → `/static/...` → WhiteNoise middleware serves efficiently
4. **API request** → `/api/...` → Django REST Framework handles

---

## Troubleshooting Checklist

**Build fails with Python error?**
```bash
git add requirements.txt
git commit -m "Update requirements"
git push heroku main
```

**Static files not loading?**
```bash
heroku run python mybackend/manage.py collectstatic --no-input
heroku restart
```

**CSRF errors?**
```bash
heroku config | grep CSRF_TRUSTED_ORIGINS
# Should show: CSRF_TRUSTED_ORIGINS=https://my-home-reno.herokuapp.com
```

**API returns 404?**
```bash
cat myfrontend/.env.production
# Should have: VITE_API_BASE_URL=https://my-home-reno.herokuapp.com/api
npx vite build  # Local rebuild
git push heroku main  # Push again
```

**Database issues?**
```bash
heroku logs --tail
heroku pg:info
heroku run python mybackend/manage.py migrate --verbose
```

---

## Monitoring

View logs:
```bash
heroku logs --tail
heroku logs --num=50  # Last 50 lines
```

Check dyno status:
```bash
heroku ps
```

Database backups:
```bash
heroku pg:backups:capture
heroku pg:backups
```

---

## Environment Variables Needed

Set these with:
```bash
heroku config:set KEY=VALUE
```

| Variable | Example | Required |
|----------|---------|----------|
| `DEBUG` | `False` | Yes |
| `ALLOWED_HOSTS` | `my-home-reno.herokuapp.com` | Yes |
| `CSRF_TRUSTED_ORIGINS` | `https://my-home-reno.herokuapp.com` | Yes |
| `OPENAI_API_KEY` | Your key | Phase 3 only |
| `SERPAPI_API_KEY` | Your key | Phase 2 only |
| `DATABASE_URL` | Auto-set | Auto |

---

## Next Deploy

After making changes:
```bash
git add .
git commit -m "Description of changes"
git push heroku main

# If you changed Python dependencies:
git push heroku main  # Heroku detects change to requirements.txt

# If you changed migrations:
heroku run python mybackend/manage.py migrate

# If you changed environment settings:
heroku config:set KEY=VALUE
heroku restart
```

---

## Key Points

✅ **Root-level `requirements.txt`** - Required for Python buildpack to activate  
✅ **`Procfile`** - Tells Heroku how to start your app  
✅ **`runtime.txt`** - Specifies Python version  
✅ **`heroku.yml`** - Declares buildpacks explicitly  
✅ **Frontend build goes to `mybackend/frontend_build/`** - Django can serve it  
✅ **`dj_database_url`** - Parses PostgreSQL connection string  
✅ **`WhiteNoise`** - Serves static files efficiently  

---

## API Endpoint Examples

After deploy, try:
```bash
# Test API is running
curl https://my-home-reno.herokuapp.com/api/projects/

# View Django admin
https://my-home-reno.herokuapp.com/admin/

# View frontend
https://my-home-reno.herokuapp.com/
```

---

## Full Heroku Deployment Guide

For more details, see [docs/heroku-config.md](heroku-config.md) for comprehensive documentation on all settings and configurations.
