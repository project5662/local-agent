class Retriever:
    def __init__(self, collection, embed_fn):
        self.collection = collection
        self.embed_fn = embed_fn

    def search(self, query: str, top_k: int):
        query_vec = self.embed_fn(query)
        results = self.collection.query(query_embeddings=[query_vec], n_results=top_k)

        matches = []

        for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            matches.append({"document": doc, "metadata": meta, "distance": dist})
        return matches