import logging as l
from dataclasses import dataclass

from elasticsearch import Elasticsearch
from fastprogress import progress_bar

from tg_rag.database.basic import SearchEngine

log = l.getLogger(__name__)


@dataclass
class ElasticConfig:
    es_url: str = "http://localhost:9200"
    es_creds: tuple = ("elastic", "elastic")
    index_name: str = "my_index"
    embedding_size: int = 768
    override: bool = True


class ElasticEngine(SearchEngine):

    def __init__(self, client_cfg: ElasticConfig):
        self.client = Elasticsearch([client_cfg.es_url],
                                    basic_auth=client_cfg.es_creds,
                                    verify_certs=False)
        self.cfg = client_cfg
        if self.cfg.override:
            self.client.indices.delete(index=self.cfg.index_name, ignore=[400, 404])
        if not self.client.indices.exists(index=self.cfg.index_name):
            self._create_index()

    def _create_index(self):
        idx_name = self.cfg.index_name
        log.info(f"Creating index {idx_name}")
        mappings = {
            "properties": {
                "text": {
                    "type": "text",
                    "term_vector": "yes"
                },
                "embedding": {
                    "type": "dense_vector",
                    "dims": self.cfg.embedding_size,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
        self.client.indices.create(index=idx_name, mappings=mappings)
        log.info(f"Index {idx_name} created.")

    def add(self, embeddings: list, documents: list):
        ops = []
        for doc, emb in zip(documents, embeddings):
            ops.append({'index': {'_index': self.cfg.index_name}})
            ops.append({
                'text': doc,
                'embedding': emb,
            })
        return self.client.bulk(operations=ops, refresh=True)

    def search(self, embedding, query, max_docs: int = 50, k: int = 10):
        if embedding is None:
            return self.search_text(query, max_docs)
        res = self.client.search(index=self.cfg.index_name,
                                 knn={
                                     'field': 'embedding',
                                     'query_vector': embedding,
                                     'num_candidates': max_docs,
                                     'k': k,
                                 }
                                 )
        return self._unwrap_elastic_result(res)

    def search_text(self, query: str, max_docs: int = 50):
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
        res = self.client.search(index=self.cfg.index_name,
                                 body=query_template(query))

        return self._unwrap_elastic_result(res)

    def _unwrap_elastic_result(self, response):
        data = response['hits']
        docs = [hit['_source']['text'] for hit in data['hits']]
        scores = [hit['_score'] for hit in data['hits']]
        return docs, scores
