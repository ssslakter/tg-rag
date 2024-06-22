from elasticsearch import Elasticsearch

from ..config import Config


class Search:
    def __init__(self, cfg: Config):
        self.es = Elasticsearch([cfg.es_url], basic_auth=cfg.es_creds, verify_certs=False)

    def search(self, text: str, max_docs: int):
        query_template = lambda x: {
            "size": max_docs,
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
        docs = [hit['_source']['text'] for hit in data['hits']]
        scores = [hit['_score'] for hit in data['hits']]

        return docs, scores

    def get_all(self):
        res = self.es.search(index="my_index", body={"size": 4000, "query": {"match_all": {}}})
        data = res.body['hits']
        docs = [hit['_source']['text'] for hit in data['hits']]
        return docs