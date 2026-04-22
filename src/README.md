# LevelUp Prototype

LevelUp is a Django prototype for booking grinds, sports coaching, and music lessons.

## Quick Start (Windows PowerShell)

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd src
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Optional Demo Data

```powershell
cd src
python manage.py seed_coaches
```

## Notes

- This repository includes a prototype SQLite database at `src/db.sqlite3`.
- Static files are served by Django in development mode.
- Templates are loaded from `src/Templates`.
