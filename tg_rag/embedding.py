from fastprogress import progress_bar
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name, bs=64):
        self.bs = bs
        self.encoder = SentenceTransformer(model_name)

    def __call__(self, texts: list):
        for i in progress_bar(range(0, len(texts), self.bs)):
            yield from self.encoder.encode(texts[i:min(i + self.bs, len(texts))])

    @property
    def dim(self):
        return self.encoder.get_sentence_embedding_dimension()
