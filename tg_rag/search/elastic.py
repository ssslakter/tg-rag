import logging as l

from elasticsearch import Elasticsearch
from fastprogress import progress_bar

from ..config import Config

log = l.getLogger(__name__)


class ElasticClient:
    def __init__(self, cfg: Config, default_index="my_index"):
        self.es = Elasticsearch([cfg.es_url],
                                basic_auth=cfg.es_creds,
                                verify_certs=False)
        self.index_name = default_index

    def create_index(self, index_name=None):
        if not index_name: index_name = self.index_name
        log.info(f"Creating index {index_name}")
        mappings = {
            "properties": {
                "text": {
                    "type": "text",
                    "term_vector": "yes"
                },
            }
        }
        self.es.indices.create(index=index_name, mappings=mappings)
        log.info(f"Index {index_name} created.")

    def delete_index(self, index_name=None):
        if not index_name: index_name = self.index_name
        if self.es.indices.exists(index=index_name):
            return self.es.indices.delete(index=index_name)

    def index_paragraphs(self, paragraphs, index_name=None):
        """Index each paragraph into the specified Elasticsearch index."""
        if not index_name: index_name = self.index_name
        log.info("Indexing paragraphs...")
        for i, paragraph in enumerate(progress_bar(paragraphs)):
            doc = {'text': paragraph}
            self.es.index(index=index_name, id=i, document=doc)
        self.es.indices.refresh(index=index_name)
        log.info("Indexing completed")

    def insert_embeddings(self, docs, embeddings, index_name=None):
        if not index_name: index_name = self.index_name
        ops = []
        for doc, emb in zip(docs, embeddings):
            ops.append({'index': {'_index': index_name}})
            ops.append({
                'summary': doc,
                'embedding': emb,
            })
        return self.es.bulk(operations=ops)

    def knn_search(self, query_embedding, index_name=None, k=10):
        if not index_name: index_name = self.index_name
        res = self.es.search(index=index_name,
                             knn={
                                 'field': 'embedding',
                                 'query_vector': query_embedding,
                                 'num_candidates': 50,
                                 'k': k,
                             }
                             )
        data = res['hits']
        docs = [hit['_source']['summary'] for hit in data['hits']]
        scores = [hit['_score'] for hit in data['hits']]
        return docs, scores
