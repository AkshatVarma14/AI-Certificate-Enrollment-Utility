"""
firebase_config.py – CertEn Firebase initialisation
=====================================================
Reads credentials from the path specified in .env
(FIREBASE_CREDENTIALS_PATH) and returns a shared Firestore client.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()


def init_firebase():
    """Initialise the Firebase Admin SDK (safe to call multiple times)."""
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase credentials file not found at '{cred_path}'.\n"
                "Download it from Firebase Console → Project Settings → Service Accounts\n"
                "and place it in the certen/ folder, then set FIREBASE_CREDENTIALS_PATH in .env"
            )
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()


# Single shared client used by app.py
db = init_firebase()
