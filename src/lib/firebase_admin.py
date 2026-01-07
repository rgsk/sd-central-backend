
import firebase_admin
from firebase_admin import credentials


def get_firebase_app():
    if not firebase_admin._apps:
        key_path = 'credentials-firebaseServiceAccountKey.json'
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
    return firebase_admin.get_app()
