import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

url = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"

data = {
    "grant_type": "client_credentials",
    "scope": os.getenv("FT_SCOPE"),
}

response = requests.post(
    url,
    data=data,
    auth=HTTPBasicAuth(
        os.getenv("FT_CLIENT_ID"),
        os.getenv("FT_CLIENT_SECRET"),
    ),
    timeout=30,
)

print(response.status_code)
print(response.text)