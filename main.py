import os
import subprocess
from adminbox import salary_path, login, get_docs, download_document

username = os.getenv("AB_USERNAME")
password = os.getenv("AB_PASSWORD")

def change_owner_permissions(folder):
    try:
        command = f"sudo chown -R docker:docker {folder} && sudo chmod -R 755 {folder}"
        subprocess.run(command, shell=True, check=True)
        print(f"Ownership &permissions updated for {folder}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred when updating ownership & permissions: {e}")

print("Checking for new documents on Adminbox...")
access_token = login(username, password)
docs = get_docs(access_token)
downloaded = download_document(access_token, docs)

if len(downloaded) > 0:
    print(f"Done. {len(downloaded)} document(s) downloaded.")
    change_owner_permissions(salary_path)
else:
    print("Done. No new documents found.")