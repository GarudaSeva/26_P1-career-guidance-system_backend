# Backend Deployment

## Requirements

- Python 3.11
- Install dependencies with `pip install -r requirements.txt`
- Start command:

```bash
gunicorn wsgi:app --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 180
```

For Heroku/Railway-style platforms, the included `Procfile` defines the web process.

## Environment Variables

- `PORT`: set automatically by most deployment platforms.
- `CORS_ORIGINS`: optional comma-separated frontend URLs. Example:

```bash
CORS_ORIGINS=https://your-frontend-domain.com
```

If `CORS_ORIGINS` is not set, the backend allows all origins.

## Files Required On The Server

Keep these folders/files with the backend because the app loads them at startup:

- `model_files/`
- `data/`
- `bramha/`
- `roles.json`
- `users.json`

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Health check:

```bash
curl http://localhost:5000/health
```

## Important Notes

- `users.json` is file-based storage. On many free hosting platforms, saved users may reset after redeploy/restart. For real production use, move user/profile data to a database.
- After backend deployment, update the frontend API base URL from `http://localhost:5000` to your deployed backend URL.
