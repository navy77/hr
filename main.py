import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account.
cred = credentials.Certificate('./serviceAccountKey.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()

div_user = {
    "f_name": "nmb",
    "s_name": "minebea",
    "div_name": "hr",
    "password": "hr",
    "created_at": firestore.SERVER_TIMESTAMP
}
doc_ref = db.collection("div_user").add(div_user)

# source_employee = {
#     "apply_position": "engineer staff",
#     "work_experience": "1",
#     "title": "ms",
#     "name": "raviwan",
#     "lastname": "krisomdee",
#     "education_on_level": "bechelor",
#     "univesity": "burapha university",
#     "major": "electical communication",
#     "gpa": 2.64,
#     "tel_no": "0951587819",
#     "email": "raviwan.krisomdee@hotmail.com",
#     "attach_file":"https://drive.google.com/drive/folders/1w1ooQn1sHtAIhHGdpjeMi2YFojvK24y0?usp=sharing",
#     "created_at": firestore.SERVER_TIMESTAMP
# }

# source_employee = {
#     "apply_position": "engineer staff",
#     "work_experience": "1",
#     "title": "mr",
#     "name": "Akaranij",
#     "lastname": "Yodmongkol",
#     "education_on_level": "bechelor",
#     "univesity": "Silpakorn University",
#     "major": "Mechanical Engineering",
#     "gpa": 2.32,
#     "tel_no": "0956345070",
#     "email": "naja.akaranij@gmail.com",
#     "attach_file":"https://drive.google.com/drive/folders/1w1ooQn1sHtAIhHGdpjeMi2YFojvK24y0?usp=sharing",
#     "created_at": firestore.SERVER_TIMESTAMP
# }
# doc_ref = db.collection("source_employee").add(source_employee)

# get
# docs = db.collection("source_employee").stream()
# for doc in docs:
#     print(f"{doc.to_dict()}")