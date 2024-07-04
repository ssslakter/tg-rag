from io import BytesIO
from typing import BinaryIO
from pypdf import PdfReader
from zipfile import ZipFile

import requests


def download_book(url):
    response = requests.get(url)
    myzip = ZipFile(BytesIO(response.content))
    file = myzip.namelist()[0]
    text = myzip.open(file).read().decode("windows-1251")
    return text


def read_txt(file: BinaryIO):
    return str(file.read())


def read_pdf(file: BinaryIO):
    reader = PdfReader(file.read())
    '\n'.join(page.extract_text() for page in reader.pages)
    
    
parse_file = {
    'txt': read_txt,
    'pdf': read_pdf
}