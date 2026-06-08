# CertEn — Certificate Enrollment Utility

A web app for managing training programs and issuing certificates to users.

---

## What You Need

- **Python** — download from [python.org](https://python.org/downloads). During install, tick **"Add Python to PATH"**.
- **Git Bash** or any terminal.

---

## Setup (One Time Only)

```bash
# 1. Go into the project folder
cd certen

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Load sample data (optional but recommended for testing)
python seed.py
```

---

## Running the App

```bash
python app.py
```

Then open your browser and go to **http://127.0.0.1:5000**

> Keep the terminal open while using the app. Press **Ctrl + C** to stop it.

---

## Logging In

| Email | Role |
|---|---|
| admin@certen.com | Admin |
| alice@gmail.com | User |
| bob@gmail.com | User |
| carol@gmail.com | User |
| david@gmail.com | User |

> These accounts are created by `seed.py`. Use your own email if you've registered manually.

---

## Adding Your Images

Drop these files into `static/images/`:

| File | Used For |
|---|---|
| `CertEn.png` | Navbar logo |
| `CertificateImage.png` | Homepage graphic |
| `signature.png` | Appears on certificates |

---

## How It Works

**As an Admin:**
- See all users and programs on the dashboard
- Click a **user** to see their enrolled programs and task progress
- Click a **program** to see who's enrolled in it
- Click into any user + program combination to view their tasks, then **Grant Certificate** when ready
- Once granted, the button becomes **View Certificate**

**As a User:**
- See your enrolled programs and task statuses (**C** = Complete, **NC** = Not Complete)
- Click **Apply for Certificate** when your tasks are done
- Once approved, click the green **View Certificate** button to open and print it

---

## Printing a Certificate

Open the certificate, then click **Print / Save PDF** at the top of the page.

---

## Common Issues

| Problem | Fix |
|---|---|
| Site can't be reached | Use `http://127.0.0.1:5000` — not `https://`, not without `:5000` |
| `python` not recognised | Reinstall Python and tick "Add Python to PATH" |
| `pip` not recognised | Use `python -m pip install ...` instead |
| App crashes on a page | Run `python seed.py` to reset the database |
| Can't log in | Use an email that exists in the database |

---

## Push to GitHub

```bash
git add .
git commit -m "your message here"
git push
```
