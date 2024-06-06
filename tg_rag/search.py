from elasticsearch import Elasticsearch
from .config import Config

cfg = Config()
es = Elasticsearch([cfg.es_url], basic_auth=cfg.es_creds, verify_certs=False)

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

res = es.search(index="my_index", body=query_template("Мастер"))
data = res.body['hits']

for i,hit in enumerate(data['hits']):
    print(f"Paragraph {hit['_id']}: {hit['_source']['text']}")