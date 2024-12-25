import requests
from requests.auth import HTTPBasicAuth
import os
from xml.etree import ElementTree as ET

nextcloud_url = "https://cloud.eliptiq.fr/remote.php/webdav"
salary_path = "/Archives/Fiches de paie/AlphaOmega"
nc_username = os.getenv("NC_USERNAME")
nc_password = os.getenv("NC_PASSWORD")

session = requests.Session()

def ls(dir = ""):
    response = requests.request("PROPFIND", nextcloud_url + salary_path + "/" + dir, auth=HTTPBasicAuth(nc_username, nc_password))
    if response.status_code == 207:
        tree = ET.fromstring(response.content)
        ls = []

        for elem in tree.findall(".//{DAV:}href"):
            elem = elem.text.replace("%20", " ")
            elem = elem.replace(f"/remote.php/webdav" + salary_path, "")
            elem = elem.replace("/", "")
            elem = elem.replace(dir, "")
            ls.append(elem)

        ls.pop(0)
        return ls
    else:
        raise Exception("Nextcloud, failed to list directory contents")

def create_folder(name):
    response = session.request("MKCOL", nextcloud_url + salary_path + "/" + name, auth=HTTPBasicAuth(nc_username, nc_password))
    if response.status_code == 201:
        print(f"Created folder: {salary_path}/{name}")
    else:
        raise Exception(f"Failed to create folder: {salary_path}/'{name}, Error: {response.status_code}")

def upload(data, path, name):
    response = requests.put(nextcloud_url + path + "/" + name, data=data, auth=HTTPBasicAuth(nc_username, nc_password))
    if response.status_code not in [200, 201, 204]:
        print(f"Failed to upload document {name}")
        print("Error", response.status_code, response.text)