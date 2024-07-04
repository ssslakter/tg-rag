
class SearchEngine:
    def __init__(self, client_cfg): raise NotImplementedError
    def search(self, embedding, query: str, max_docs: int, nickname: str): raise NotImplementedError
    def get_all(self, nickname: str): raise NotImplementedError
    def add(self, embeddings: list, documents: list, nickname: str): raise NotImplementedError
    def clear(self, nickname: str): raise NotImplementedError
