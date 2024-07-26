import firebase_admin
from firebase_admin import credentials
import os
import json
from dotenv import load_dotenv


load_dotenv()
lingobell_firebase_auth_path = os.getenv('LINGOBELL_FIREBASE_AUTH_PATH')

if lingobell_firebase_auth_path and os.path.exists(lingobell_firebase_auth_path):
    cred = credentials.Certificate(lingobell_firebase_auth_path)
    firebase_admin.initialize_app(cred)
    print("Firebase initialized")
else:
    print("No Firebase configuration found or invalid path")
