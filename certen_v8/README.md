# CertEn v7 — Firebase Firestore Edition

Certificate Enrollment Utility — now powered by Firebase Firestore instead of SQLite.

---

## What You Need

- Python (with "Add to PATH" ticked on Windows)
- A Firebase project with Firestore enabled (see setup below)
- Your `firebase-credentials.json` placed in the `certen/` folder

---

## First-Time Setup

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Copy the env template and fill it in
cp .env.example .env
# Open .env and set FIREBASE_CREDENTIALS_PATH and FLASK_SECRET_KEY

# 3. Seed Firestore with sample data
python seed_firebase.py

# 4. Run the app
python app.py
```

Then open **http://127.0.0.1:5000**

---

## Test Logins

| Email | Role |
|---|---|
| admin@certen.com | Admin |
| alice@gmail.com | User |
| bob@gmail.com | User |
| carol@gmail.com | User |
| david@gmail.com | User |

---

## Project Files

| File | Purpose |
|---|---|
| `app.py` | Flask routes — no SQLAlchemy anywhere |
| `firebase_config.py` | Initialises Firebase Admin SDK |
| `firestore_helpers.py` | All Firestore read/write functions |
| `seed_firebase.py` | Populates Firestore with sample data |
| `.env.example` | Template for your credentials |
| `requirements.txt` | Python packages needed |

---

## Images

Place these in `static/images/`:
- `CertEn.png` — navbar logo
- `CertificateImage.png` — homepage graphic
- `signature.png` — appears on certificates

---

## Push to GitHub

```bash
git add .
git commit -m "v7 Firebase migration"
git push
```

Make sure `.env` and `firebase-credentials.json` are in `.gitignore` before pushing.
