import logging as l
from zipfile import ZipFile
from io import BytesIO
import requests
from fastprogress import progress_bar
from .config import Config
from .utils import init_logger


init_logger()
init_logger(name="elastic_transport.transport", level=l.ERROR)
cfg = Config()

l.info(f"Downloading the book from {cfg.book_url}")
response = requests.get(cfg.book_url)
myzip = ZipFile(BytesIO(response.content))
file = myzip.namelist()[0]
text = myzip.open(file).read().decode("windows-1251")
paragraphs = text.split("\r\n")

max_paragraph = max(paragraphs, key=len)
l.info(f"Downloaded {len(paragraphs)} paragraphs, the longest one has {len(max_paragraph)} characters")

from elasticsearch import Elasticsearch

l.info(f"Connecting to {cfg.es_creds}@{cfg.es_url}")
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

l.info("Index my_index created. Indexing paragraphs...")
# Index each paragraph
for i, paragraph in enumerate(progress_bar(paragraphs)):
    doc = {
        'text': paragraph,
    }
    res = es.index(index="my_index", id=i, document=doc)

# Refresh the index to make the documents searchable
es.indices.refresh(index="my_index")
l.info("Indexing completed")

main = 0

if __name__ == "__main__":
    pass