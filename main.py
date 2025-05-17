import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account.
cred = credentials.Certificate('./serviceAccountKey.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()

doc_ref = db.collection("hr_db").document("div_user")

div_user = {"f_name":"nmb",
            "s_name":"minebea",
            "div_name":"div01"}

doc_ref.set(div_user)