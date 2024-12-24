import requests
import re
import hashlib
import os
from bs4 import BeautifulSoup
import base64
from nextcloud import ls, create_folder, upload, salary_path

url_auth = "https://iam.unifiedpost.com/auth/realms/consumer-sso/protocol/openid-connect/auth"
url_token = "https://iam.unifiedpost.com/auth/realms/consumer-sso/protocol/openid-connect/token"
redirect_uri = "https://adminbox.myarchive.lu/v10/users/sign_in/callback"
client_id = "adminbox-lux-fe"

def generate_code_verifier():
    return base64.urlsafe_b64encode(os.urandom(96)).rstrip(b"=").decode("utf-8")

# Function to generate code challenge from code verifier
def generate_code_challenge(code_verifier):
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).rstrip(b"=").decode("utf-8")
    return code_challenge

def login(username, password):
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    session = requests.Session()
    params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": "openid phone",
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    response = session.get(url_auth, params=params)

    # Parse the response HTML to find the login form action URL
    soup = BeautifulSoup(response.text, "html.parser")
    login_form = soup.find("form", id="kc-form-login")
    if not login_form:
        raise Exception("Could not find the login form.")

    login_url = login_form["action"]
    login_payload = {
        "username": username,
        "password": password,
    }
    login_response = session.post(login_url, data=login_payload, allow_redirects=False)

    # Check if the response contains a redirect to the callback URL with a code
    if 300 <= login_response.status_code < 400:
        # Get the "Location" header for the redirect URL
        redirect_url = login_response.headers.get("Location")
        code = re.search(r"code=([^&]+)", redirect_url)
        if not code:
            raise Exception("Authorization code not found in the redirect URL.")
        code = code.group(1)
    else:
        raise Exception("Login failed, no redirect occurred.")

    # Exchange the authorization code for an access token
    token_payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }
    token_response = session.post(url_token, data=token_payload)

    if token_response.status_code == 200:
        print("Adminbox login successful")
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        # print("Access Token:", access_token)
        return access_token
    else:
        raise Exception("Failed to obtain token:", token_response.text)

def get_docs(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.get("https://adminbox.myarchive.lu/inbox_items", headers=headers)

    if response.status_code == 200:
        return retrieve_new_docs(response.json())
    else:
        print("Failed to retrieve documents:", response.status_code, response.text)
        return None

def retrieve_new_docs(docs):
    new_docs = []
    docs = delete_duplicates(docs)
    check_folders(docs)

    for doc in docs["inbox_filtered_items"]:
        year = doc["date"].split("-")[0]
        month = int(doc["date"].split("-")[1])

        local_docs = ls(year)
        if local_docs is None:
            new_docs.append(doc)
        else:
            if f"{get_name(month)}.pdf" not in local_docs:
                new_docs.append(doc)

    docs["inbox_filtered_items"] = new_docs
    return new_docs

def check_folders(docs):
    years = set(doc["date"].split("-")[0] for doc in docs["inbox_filtered_items"])

    existing_folders = ls()
    for year in years:
        if year not in existing_folders:
            create_folder(year)

def delete_duplicates(docs):
    unique_docs = []
    seen = set()

    for doc in docs["inbox_items"]:
        identifier = (doc["type"], doc.get("title", ""), doc["date"], doc["nr"])
        if identifier not in seen:
            seen.add(identifier)
            unique_docs.append(doc)

    del docs["inbox_items"]
    docs["inbox_filtered_items"] = unique_docs
    return docs

def get_name(month):
    months = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "Décember",
    }
    return months.get(month)

def get_destination(type, year):
    if type == "salary_slip":
        return f"/{salary_path}/{year}"

def download_document(access_token, docs):
    uploaded_docs = []

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    for doc in docs:
        download_url = doc["download_url"]
        year = int(doc["date"].split("-")[0])
        month = int(doc["date"].split("-")[1])
        type = doc["type"]
        name = get_name(month)

        response = requests.get(download_url, headers=headers)
        print(f"Downloaded: {name}.pdf")

        if response.status_code == 200:
            try:
                pdf_data = base64.b64decode(response.text)
                upload(pdf_data, get_destination(type, year), f"{name}.pdf")

                uploaded_docs.append(name)

            except Exception as e:
                print(f"Failed to decode Base64 content: {e}")
        else:
            print(f"Failed to download document {name}.pdf")
            print("Error:", response.status_code, response.text)

    return uploaded_docs