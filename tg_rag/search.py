from elasticsearch import Elasticsearch
from .config import Config


class Search:
    def __init__(self, cfg: Config):
        self.es = Elasticsearch([cfg.es_url], basic_auth=cfg.es_creds, verify_certs=False)

    def search(self, text: str):
        query_template = lambda x: {
            "size": 100,
            "query": {
                "more_like_this": {
                    "fields": ["text"],
                    "like": x,
                    "min_term_freq": 1
                }
            }
        }

        res = self.es.search(index="my_index", body=query_template(text))
        data = res.body['hits']

        return data
