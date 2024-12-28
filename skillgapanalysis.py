import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

def initialize_faiss(index_dim):
    """Initialize FAISS index for dense vector searching."""
    index = faiss.IndexFlatIP(index_dim)  
    if not index.is_trained:
        print("Training index...")
    return index

def vectorize_data(data, model):
    """Vectorize the input data using Sentence-BERT."""
    return model.encode(data, convert_to_tensor=False)

def populate_faiss_index(index, vectors):
    """Populate FAISS index with vectors."""
    index.add(np.array(vectors, dtype=np.float32))

def retrieve_skill_requirements(neo4j_driver, query):
    """Query Neo4j to retrieve industry skill requirements."""
    with neo4j_driver.session() as session:
        results = session.run(query)
        return [record['skill'] for record in results]

def find_skill_gaps(user_embedding, skill_embeddings, skill_names, index, top_k=5):
    """Identify skill gaps by comparing user embedding to skills."""
    D, I = index.search(user_embedding, top_k)
    gaps = [(skill_names[i], D[0][idx]) for idx, i in enumerate(I[0])]
    return gaps

if __name__ == "__main__":
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "priyanshi"))

    user_data = ["Python", "Machine Learning", "Data Analysis"] 
    user_embedding = vectorize_data(user_data, model)
    user_embedding = np.mean(user_embedding, axis=0, keepdims=True) 

    query = """
    MATCH (s:Skill)-[:REQUIRED_FOR]->(j:Job)
    RETURN DISTINCT s.name AS skill
    """
    industry_skills = retrieve_skill_requirements(neo4j_driver, query)

    skill_embeddings = vectorize_data(industry_skills, model)
    skill_names = industry_skills

    index = initialize_faiss(skill_embeddings[0].shape[0])
    populate_faiss_index(index, skill_embeddings)

    skill_gaps = find_skill_gaps(user_embedding, skill_embeddings, skill_names, index, top_k=5)

    print("Skill Gaps and Similarity Scores:")
    for skill, score in skill_gaps:
        print(f"Skill: {skill}, Similarity: {score:.2f}")

    neo4j_driver.close()