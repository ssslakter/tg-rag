import logging as l
from io import BytesIO
from zipfile import ZipFile

import requests
from elasticsearch import Elasticsearch
from fastprogress import progress_bar

from .config import Config
from .utils import init_logger


def download_book(url):
    l.info(f"Downloading the book from {url}")
    response = requests.get(url)
    myzip = ZipFile(BytesIO(response.content))
    file = myzip.namelist()[0]
    text = myzip.open(file).read().decode("windows-1251")
    paragraphs = text.split("\r\n")

    max_paragraph = max(paragraphs, key=len)
    l.info(f"Downloaded {len(paragraphs)} paragraphs, the longest one has {len(max_paragraph)} characters")
    return paragraphs


def create_index(es_client, index_name):
    l.info(f"Creating index {index_name}")
    mappings = {
        "properties": {
            "text": {
                "type": "text",
                "term_vector": "yes"
            },
        }
    }
    es_client.indices.create(index=index_name, mappings=mappings)
    l.info(f"Index {index_name} created.")


def index_paragraphs(es, index_name, paragraphs):
    """Index each paragraph into the specified Elasticsearch index."""
    l.info("Indexing paragraphs...")
    for i, paragraph in enumerate(progress_bar(paragraphs)):
        doc = {'text': paragraph}
        es.index(index=index_name, id=i, document=doc)
    es.indices.refresh(index=index_name)
    l.info("Indexing completed")


def main():
    init_logger()
    init_logger(name="elastic_transport.transport", level=l.ERROR)
    cfg = Config()

    paragraphs = download_book(cfg.book_url)

    l.info(f"Connecting to {cfg.es_creds}@{cfg.es_url}")
    es = Elasticsearch([cfg.es_url], basic_auth=cfg.es_creds, verify_certs=False)

    create_index(es, "my_index")
    index_paragraphs(es, "my_index", paragraphs)


if __name__ == "__main__":
    main()
