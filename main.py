import os
import subprocess
from adminbox import salary_path, login, get_docs, download_document

username = os.getenv("AB_USERNAME")
password = os.getenv("AB_PASSWORD")

print("Checking for new documents on Adminbox...")
access_token = login(username, password)
docs = get_docs(access_token)
downloaded = download_document(access_token, docs)

if len(downloaded) > 0:
    print(f"Done. {len(downloaded)} document(s) received.")
else:
    print("Done. No new documents found.")