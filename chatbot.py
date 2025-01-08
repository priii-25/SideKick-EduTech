import itertools
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from langchain_community.llms import Ollama

def decompose_query(query: str):
    steps = []
    tokens = query.lower().replace(',', ' ').split()
    current_segment = []
    for token in tokens:
        if token in ["and", "then", "also"]:
            if current_segment:
                steps.append(" ".join(current_segment))
                current_segment = []
        else:
            current_segment.append(token)
    if current_segment:
        steps.append(" ".join(current_segment))

    return steps

class SemanticSearch:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.encoder = SentenceTransformer(model_name)
        self.index = None
        self.documents = []

    def build_index(self, docs: list):
        self.documents = docs
        embeddings = self.encoder.encode(docs, convert_to_numpy=True)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 3):
        if self.index is None:
            raise ValueError("Search index is not built. Call build_index first.")

        query_embedding = self.encoder.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_embedding, top_k)
        results = []
        for dist_list, idx_list in zip(distances, indices):
            for dist, idx in zip(dist_list, idx_list):
                results.append((self.documents[idx], dist))
        return results

def rag_pipeline(query: str, semantic_search_instance: SemanticSearch, generation_fn, top_k: int = 3):
    steps = decompose_query(query)
    all_relevant_docs = []

    for step in steps:
        results = semantic_search_instance.search(step, top_k=top_k)
        doc_texts = [doc for doc, dist in results]
        all_relevant_docs.append("\n".join(doc_texts))

    combined_context = "\n".join(all_relevant_docs)
    return generation_fn(query, combined_context)

def dummy_llm_generation(query: str, context: str):
    llama2 = Ollama(model="llama2")
    response = llama2(query)
    return response

if __name__ == "__main__":
    documents = [
        "Data Scientist position, requires Python, machine learning, and data visualization skills.",
        "Software Engineer position, proficiency in C++ and system design.",
        "Front-end Developer position, requires JavaScript, React, and CSS expertise.",
        "Full-stack Developer position, needs experience with Node.js and cloud deployment."
    ]

    sem_search = SemanticSearch()
    sem_search.build_index(documents)

    user_query = "Show me roles that require Python and also need cloud deployment"

    answer = rag_pipeline(query=user_query, semantic_search_instance=sem_search,
                          generation_fn=dummy_llm_generation, top_k=2)

    print("=== FINAL ANSWER ===")
    print(answer)