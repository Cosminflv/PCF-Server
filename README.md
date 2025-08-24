# Image Gallery API

Self-hosted image gallery with per-user encrypted images, subject classification and simple filters.

## Features
- Register / JWT login
- Upload encrypted images (client provides gallery password)
- Apply filters (sepia, black and white, invert)
- Subjects (auto-prediction if `subject_name=noSubject`)
- Auto-generated OpenAPI docs at `/docs` and `/redoc`

## Quickstart (development)

```bash
# create venv & install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# configure env vars
export DATABASE_URL=sqlite:///./dev.db
export SECRET_KEY="supersecret"  # see security.md for guidance

# run migrations (alembic)
alembic upgrade head

# run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
