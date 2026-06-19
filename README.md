# CertEn — Certificate Enrollment Utility

A Flask web application for managing employee training programs and issuing
completion certificates. Users sign up, enroll in programs, complete tasks,
and apply for certificates; admins review progress and grant certificates.
Data is stored in Firebase Firestore.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Templates | Jinja2 |
| Styling | Tailwind CSS (CDN) |
| Database | Firebase Firestore |
| Auth | Werkzeug password hashing (salted hashes) + Flask sessions |
| Forms | Flask-WTF (CSRF protection) |

---

## What You Need

- **Python 3.10+** — from [python.org](https://python.org/downloads). On Windows, tick **"Add Python to PATH"** during install.
- A **Firebase project** with Firestore enabled.
- A terminal (Git Bash, PowerShell, or any shell).

---

## First-Time Setup

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Copy the env template and fill it in
cp .env.example .env
# Open .env and set FLASK_SECRET_KEY to a long random string.
# FIREBASE_CREDENTIALS_PATH should point to your service account JSON.

# 3. Download your Firebase service account key from
#    Firebase Console -> Project Settings -> Service Accounts,
#    and save it as firebase-credentials.json in this folder.

# 4. Seed Firestore with sample data (one time only)
python seed_firebase.py

# 5. Run the app
python app.py
```

Then open **http://127.0.0.1:5000**

> The app refuses to start if `FLASK_SECRET_KEY` is missing from `.env` —
> this is intentional, to prevent running with an insecure default key.

---

## Test Accounts (created by `seed_firebase.py`)

| Email | Password | Role |
| admin@certen.com | Admin@123 | Admin |
| alice@gmail.com | User@123 | User |
| bob@gmail.com | User@123 | User |
| carol@gmail.com | User@123 | User |
| david@gmail.com | User@123 | User |

These are generic seeded passwords — change them via **Forgot Password** after
your first login. New accounts can also be created directly through the
**Sign Up** page.

---

## How It Works

**Signing up / signing in**
- New users register an account via **Sign Up** (first name, last name, email, DOB, password).
- Returning users sign in from the homepage with email + password.
- Forgot your password? Use **Forgot Password** to set a new one.

**As a User**
- View enrolled programs and task statuses (**C** = Complete, **NC** = Not Complete) on your dashboard.
- Enroll in a new program from **Enroll in a Program**.
- Click **Apply for Certificate** once your tasks are done — if tasks are incomplete, your request is queued for admin review instead.
- Once granted, click **View Certificate** to open and print it.

**As an Admin**
- View all users and programs on the Admin Dashboard, in either a user-centric or program-centric view.
- Click a **user** to see their enrolled programs and task progress.
- Click a **program** to see who's enrolled in it.
- Open any user + program combination to review tasks, then **Grant Certificate**.
- Admin accounts cannot enroll in programs — the **Enroll** option is hidden for admins.

---

## Printing a Certificate

Open the certificate, then use your browser's **Print** option (Ctrl/Cmd + P)
or the in-page **Print** button to save it as a PDF.

---

## Security Notes

- Passwords are hashed with Werkzeug's salted hashing (`generate_password_hash` / `check_password_hash`).
- All state-changing forms (sign in, sign up, forgot password, enroll, apply for certificate, grant certificate) are protected by Flask-WTF CSRF tokens.
- `/admin` and `/admin/grant_certificate` require an authenticated admin session; non-admins are redirected to their own dashboard, and signed-out visitors are redirected to the homepage.
- `/register` (the enrollment form) requires an authenticated session.
- Never commit `.env` or `firebase-credentials.json` — both are excluded via `.gitignore`.

---

## Project Structure

```
.
├── app.py                   # Flask routes
├── firebase_config.py       # Firebase Admin SDK initialisation
├── firestore_helpers.py     # All Firestore read/write functions
├── seed_firebase.py         # Populates Firestore with sample data
├── requirements.txt         # Python dependencies
├── .env.example             # Template for environment variables
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── images/               # CertificateImage.png included; add CertEn.png + signature.png yourself
├── templates/
│   ├── base.html             # Shared navbar, flash messages
│   ├── index.html            # Homepage / sign-in
│   ├── signup.html           # Account creation
│   ├── forgot_password.html  # Password reset
│   ├── register.html         # Program enrollment form
│   ├── profile.html          # User profile
│   ├── user_dashboard.html   # User view — programs, tasks, certificate
│   ├── admin_dashboard.html  # Admin view — user/program panels
│   └── certificate.html      # Printable certificate page
└── SiteDesign/               # Original Canva UI mockups (design reference only)
```

---

## Common Issues

| Problem | Fix |
| Site can't be reached | Use `http://127.0.0.1:5000` — not `https://`, and don't drop the `:5000` |
| `python` not recognised | Reinstall Python and tick "Add Python to PATH" |
| `pip` not recognised | Use `python -m pip install ...` instead |
| `RuntimeError: FLASK_SECRET_KEY is not set` | Create `.env` from `.env.example` and set a value for `FLASK_SECRET_KEY` |
| `FileNotFoundError` for Firebase credentials | Place `firebase-credentials.json` in the project root and check `FIREBASE_CREDENTIALS_PATH` in `.env` |
| Can't sign in with a seeded account | Run `python seed_firebase.py` again, or use **Forgot Password** to set a new password |
| App crashes / data looks wrong | Re-run `python seed_firebase.py` to reset Firestore sample data |

---

## Push to GitHub

```bash
git add .
git commit -m "your message here"
git push
```

`.env` and `firebase-credentials.json` are excluded via `.gitignore` and will
never be staged, even with `git add .`.
