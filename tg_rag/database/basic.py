
class SearchEngine:
    def __init__(self, client_cfg): raise NotImplementedError
    def search(self, embedding, query: str, max_docs: int): raise NotImplementedError
    def get_all(self): raise NotImplementedError
    def add(self, embeddings: list, documents: list): raise NotImplementedError
