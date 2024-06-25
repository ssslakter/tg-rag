from io import BytesIO
from zipfile import ZipFile

import requests


def download_book(url):
    response = requests.get(url)
    myzip = ZipFile(BytesIO(response.content))
    file = myzip.namelist()[0]
    text = myzip.open(file).read().decode("windows-1251")
    return text