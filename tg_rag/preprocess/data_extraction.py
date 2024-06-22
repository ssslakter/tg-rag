import logging as l
from io import BytesIO
from zipfile import ZipFile

import requests

from ..config import Config
from ..search.elastic import ElasticClient
from ..utils import init_logger
from .text_parsing import parse_book

log = l.getLogger(__name__)


def download_book(url):
    log.info(f"Downloading the book from {url}")
    response = requests.get(url)
    myzip = ZipFile(BytesIO(response.content))
    file = myzip.namelist()[0]
    text = myzip.open(file).read().decode("windows-1251")
    return text


def main():
    init_logger(log.name)
    init_logger(name="elastic_transport.transport", level=log.ERROR)
    cfg = Config()

    book = download_book(cfg.book_url)
    paragraphs = parse_book(book)

    log.info(f"Connecting to {cfg.es_creds}@{cfg.es_url}")
    es = ElasticClient(cfg)
    es.create_index("my_index")
    es.index_paragraphs("my_index", paragraphs)


if __name__ == "__main__":
    main()
