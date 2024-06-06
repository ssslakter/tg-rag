from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import requests
from fastprogress import progress_bar
from .config import Config

cfg = Config()

# Download the zip file
response = requests.get(cfg.book_url)
myzip = ZipFile(BytesIO(response.content))
file = myzip.namelist()[0]
text = myzip.open(file).read().decode("windows-1251")
paragraphs = text.split("\r\n")

max_paragraph = max(paragraphs, key=len)
print(len(paragraphs), len(max_paragraph))


# add paragraphs to elasticsearch

from elasticsearch import Elasticsearch
es = Elasticsearch([cfg.es_url], basic_auth=cfg.es_creds, verify_certs=False)

mappings = {
    "properties": {
        "text": {
            "type": "text",
            "term_vector": "yes"
        },
    }
}

es.indices.create(index="my_index", mappings=mappings)

# Index each paragraph
for i, paragraph in enumerate(progress_bar(paragraphs)):
    doc = {
        'text': paragraph,
    }
    res = es.index(index="my_index", id=i, document=doc)

# Refresh the index to make the documents searchable
es.indices.refresh(index="my_index")
