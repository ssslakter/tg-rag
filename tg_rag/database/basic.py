
class SearchEngine:
    def __init__(self, client_cfg): raise NotImplementedError
    def search(self, nickname: str, embedding, query: str, max_docs: int): raise NotImplementedError
    def get_all(self, nickname: str): raise NotImplementedError
    def add(self, nickname: str, filename: str, embeddings: list, documents: list): raise NotImplementedError
    def clear(self, nickname: str): raise NotImplementedError
    def delete(self, nickname: str, filename: str): raise NotImplementedError