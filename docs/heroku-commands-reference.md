# Heroku Deployment - Command Reference

Copy and paste these commands in order. Replace `my-home-reno` with your app name.

---

## Setup Commands (Run once)

### 1. Login to Heroku
```bash
heroku login
```

### 2. Create Heroku App
```bash
heroku create my-home-reno
```
Or if app already exists:
```bash
heroku git:remote -a my-home-reno
```

### 3. Add PostgreSQL Database
```bash
heroku addons:create heroku-postgresql:hobby-dev --app=my-home-reno
```

### 4. Set Environment Variables
```bash
heroku config:set DEBUG=False --app=my-home-reno
heroku config:set ALLOWED_HOSTS=my-home-reno.herokuapp.com --app=my-home-reno
heroku config:set CSRF_TRUSTED_ORIGINS=https://my-home-reno.herokuapp.com --app=my-home-reno
```

### 5. Set API Keys (if using Phase 2 or 3 features)
```bash
heroku config:set OPENAI_API_KEY=sk-... --app=my-home-reno
heroku config:set SERPAPI_API_KEY=... --app=my-home-reno
```

### 6. Verify Environment Variables
```bash
heroku config --app=my-home-reno
```

---

## Deploy Commands (First deployment)

### 1. Ensure Git repo is clean
```bash
cd /Users/lunayou/Documents/MyHomeReno
git status
# Should show "On branch main/master, nothing to commit"
```

If you have uncommitted changes:
```bash
git add .
git commit -m "Ready for Heroku deployment"
```

### 2. Deploy to Heroku
```bash
git push heroku main
# Or if your default branch is master:
git push heroku master
```

This will:
- Upload code to Heroku
- Install Python dependencies from `requirements.txt`
- Install Node.js and build React frontend
- Run migrations (Procfile release command)
- Start Gunicorn server

**Watch the logs:**
```bash
heroku logs --tail --app=my-home-reno
```

Press `Ctrl+C` to stop.

### 3. Run Migrations
Usually happens automatically, but to be sure:
```bash
heroku run python mybackend/manage.py migrate --app=my-home-reno
```

### 4. Create Superuser (optional, for admin access)
```bash
heroku run python mybackend/manage.py createsuperuser --app=my-home-reno
```

### 5. View Your App
```bash
heroku open --app=my-home-reno
```

---

## Subsequent Deployments

After making code changes:

### 1. Commit changes
```bash
git add .
git commit -m "Description of what changed"
```

### 2. Deploy
```bash
git push heroku main
```

### 3. If you added Python dependencies
The deploy will:
- Detect change to `requirements.txt` OR `mybackend/requirements.txt`
- Reinstall Python packages
- Rebuild everything

### 4. If you created new migrations
```bash
heroku run python mybackend/manage.py migrate --app=my-home-reno
```

### 5. If you changed environment variables
```bash
heroku config:set KEY=NEW_VALUE --app=my-home-reno
heroku restart --app=my-home-reno
```

---

## Monitoring Commands

### View Logs (Real-time)
```bash
heroku logs --tail --app=my-home-reno
```

### View Recent Logs (Last 50 lines)
```bash
heroku logs --num=50 --app=my-home-reno
```

### Check Dyno Status
```bash
heroku ps --app=my-home-reno
```

Should show:
```
web.1       up for X minutes
release.1   completed
```

### Restart Dyno
```bash
heroku restart --app=my-home-reno
```

### Stop Dyno
```bash
heroku ps:stop web.1 --app=my-home-reno
```

### Start Dyno
```bash
heroku ps:start web.1 --app=my-home-reno
```

---

## Database Commands

### View Database Info
```bash
heroku pg:info --app=my-home-reno
```

### Create Database Backup
```bash
heroku pg:backups:capture --app=my-home-reno
```

### View Backups
```bash
heroku pg:backups --app=my-home-reno
```

### Access Database Shell
```bash
heroku pg:psql --app=my-home-reno
```

Type `\quit` to exit.

### View DATABASE_URL
```bash
heroku config:get DATABASE_URL --app=my-home-reno
```

---

## Configuration Commands

### View All Environment Variables
```bash
heroku config --app=my-home-reno
```

### Set a Variable
```bash
heroku config:set KEY=VALUE --app=my-home-reno
```

### Unset a Variable
```bash
heroku config:unset KEY --app=my-home-reno
```

### View Specific Variable
```bash
heroku config:get KEY --app=my-home-reno
```

---

## Static Files Commands

### Collect Static Files (Manual)
```bash
heroku run python mybackend/manage.py collectstatic --no-input --app=my-home-reno
```

### View Static Files
```bash
heroku run ls -la mybackend/staticfiles/ --app=my-home-reno
```

### Clear Static Cache
```bash
heroku restart --app=my-home-reno
```

---

## Buildpack Commands

### View Current Buildpacks
```bash
heroku buildpacks --app=my-home-reno
```

### Set Python Buildpack (if needed)
```bash
heroku buildpacks:set heroku/python --app=my-home-reno
heroku buildpacks:add heroku/nodejs --app=my-home-reno
```

---

## Testing Commands

### Test API Endpoint
```bash
curl https://my-home-reno.herokuapp.com/api/projects/
```

### Test Admin Panel
```bash
open https://my-home-reno.herokuapp.com/admin/
```

### Test Frontend
```bash
open https://my-home-reno.herokuapp.com/
```

---

## Rollback Command

If deployment goes wrong and you want to undo:

### Current Release Info
```bash
heroku releases --app=my-home-reno
```

Shows numbered releases.

### Rollback to Previous Release
```bash
heroku rollback --app=my-home-reno
```

### Rollback to Specific Release
```bash
heroku rollback v2 --app=my-home-reno
```

---

## Destroy App (Be careful!)

If you want to delete the app entirely:

```bash
heroku destroy --app=my-home-reno --confirm=my-home-reno
```

---

## Common Issues & Fixes

### Build fails - Python error
```bash
# Ensure requirements.txt is committed
git add requirements.txt
git commit -m "Update dependencies"
git push heroku main
```

### Static files not loading
```bash
heroku run python mybackend/manage.py collectstatic --no-input --app=my-home-reno
heroku restart --app=my-home-reno
```

### CSRF token errors
```bash
heroku config --app=my-home-reno | grep CSRF
# Should show: CSRF_TRUSTED_ORIGINS=https://my-home-reno.herokuapp.com
```

### API returns 404
```bash
# Check frontend env
cat myfrontend/.env.production
# Should have: VITE_API_BASE_URL=https://my-home-reno.herokuapp.com/api

# Rebuild locally and push
cd myfrontend && npm run build
cd ..
git add myfrontend/dist/
git commit -m "Rebuild frontend"
git push heroku main
```

### Database connection errors
```bash
heroku logs --tail --app=my-home-reno
heroku pg:info --app=my-home-reno
heroku run python mybackend/manage.py migrate --verbose --app=my-home-reno
```

### Out of memory
```bash
heroku ps --app=my-home-reno  # Check dyno type
heroku dyno:type standard-1x --app=my-home-reno  # Upgrade (paid)
```

---

## Summary

**First Deploy:**
```bash
git push heroku main
heroku run python mybackend/manage.py migrate
heroku open
```

**Subsequent Deploys:**
```bash
git add .
git commit -m "Changes"
git push heroku main
```

**Monitoring:**
```bash
heroku logs --tail
heroku ps
```

---

## App URL
```
https://my-home-reno.herokuapp.com
https://my-home-reno.herokuapp.com/admin
https://my-home-reno.herokuapp.com/api/projects/
```

Replace `my-home-reno` with your actual app name.
