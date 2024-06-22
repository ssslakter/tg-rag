from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

from tg_rag.config import Config
from tg_rag.utils import init_logger


class Search:
    def __init__(self, index_name, cfg: Config):
        self.es = Elasticsearch([cfg.es_url], basic_auth=cfg.es_creds, verify_certs=False)
        self.es.health_report()
        self.model = SentenceTransformer(cfg.embedding_model)
        self.index_name = index_name
        
    def create_index(self):
        mappings = {
            "properties": {
                "summary": {
                    "type": "text",
                    "term_vector": "yes"
                },
                "embedding": {
                    "type": "dense_vector",
                    "dims": self.model.get_sentence_embedding_dimension()
                }
            }
        }
        self.es.indices.create(index=self.index_name, mappings=mappings)

    def get_embedding(self, text):
        return self.model.encode(text)

    def insert_document(self, document):
        return self.es.index(index=self.index_name, document={
            **document,
            'embedding': self.get_embedding(document['summary']),
        })

    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({'index': {'_index': self.index_name}})
            operations.append({
                **document,
                'embedding': self.get_embedding(document['summary']),
            })
        return self.es.bulk(operations=operations)

    def knn_search(self, query):
        query_embedding = self.get_embedding(query)
        res = self.es.search(index=self.index_name, 
                             knn={
                                 'field': 'embedding',
                                 'query_vector': query_embedding,
                                 'num_candidates': 50,  
                                 'k': 10,
                                 }
                             )
        data = res['hits']
        docs = [hit['_source']['summary'] for hit in data['hits']]
        scores = [hit['_score'] for hit in data['hits']]
        return docs, scores
    
    def delete_index(self):
        if self.es.indices.exists(index=self.index_name):
            return self.es.indices.delete(index=self.index_name)


if __name__ == "__main__":
    from tg_rag.search import text
    init_logger()
    cfg = text.Config()
    ts = text.Search(cfg)
    search = Search('vec_index', cfg)
    search.delete_index()
    search.create_index()
    paragraphs = ts.get_all()
    for p in paragraphs:
        search.insert_document({'summary': p})
    
    res = search.knn_search("Мастер и Маргарита")
    print(res)
    
