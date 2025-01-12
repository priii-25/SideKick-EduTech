# Filename: main.py
from typing import List
from fastapi import FastAPI, Body
from pydantic import BaseModel
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------
class UserSkills(BaseModel):
    skills: List[str]
    top_k: int = 5

# ------------------------------------------------------------------
# Core functions
# ------------------------------------------------------------------
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
    # Ensure vectors has shape (N, D) and is not empty
    if len(vectors) == 0:
        print("No skill vectors to add to the index.")
        return
    index.add(np.array(vectors, dtype=np.float32))

def retrieve_skill_requirements(neo4j_driver, query):
    """Query Neo4j to retrieve industry skill requirements."""
    with neo4j_driver.session(database="jobsskills") as session:
        results = session.run(query)
        # Return list of skill names or an empty list if none matched
        return [record['skill'] for record in results]

def find_skill_gaps(user_embedding, skill_embeddings, skill_names, index, top_k=5):
    """Identify skill gaps by comparing user embedding to skills."""
    D, I = index.search(user_embedding, top_k)
    # Each element in D is the similarity score, I is the skill index
    # Convert D[0][idx] to float to ensure JSON serialization
    gaps = [(skill_names[i], float(D[0][idx])) for idx, i in enumerate(I[0])]
    return gaps

# ------------------------------------------------------------------
# Initialize FastAPI
# ------------------------------------------------------------------
app = FastAPI(title="Skill Gap API")

# ------------------------------------------------------------------
# Pre-load model and set up the FAISS index + Neo4j driver
# ------------------------------------------------------------------
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "priyanshi"))

# Retrieve existing skills from Neo4j
query = """
MATCH (s:Skill)-[:REQUIRED_FOR]->(j:Job)
RETURN DISTINCT s.name AS skill
"""
industry_skills = retrieve_skill_requirements(neo4j_driver, query)

# Vectorize industry skills once and build FAISS index
if len(industry_skills) > 0:
    skill_embeddings = vectorize_data(industry_skills, model)
    skill_dim = skill_embeddings[0].shape[0]  # Dimension of each vector
else:
    skill_embeddings = []
    skill_dim = 0

faiss_index = initialize_faiss(skill_dim)
populate_faiss_index(faiss_index, skill_embeddings)

# ------------------------------------------------------------------
# API Endpoint: Calculate Skill Gaps
# ------------------------------------------------------------------
@app.post("/skill-gaps")
def get_skill_gaps(user_request: UserSkills = Body(...)):
    """
    POST JSON data with:
    {
      "skills": ["Python", "Machine Learning", "Data Analysis"],
      "top_k": 5
    }
    """
    # Vectorize user skills
    user_vector = vectorize_data(user_request.skills, model)
    # Average user vectors for a representative embedding
    user_embedding = np.mean(user_vector, axis=0, keepdims=True).astype(np.float32)

    # If no skills were retrieved from Neo4j, return an empty response
    if len(skill_embeddings) == 0:
        return {"skill_gaps": []}

    # Find skill gaps
    gaps = find_skill_gaps(
        user_embedding=user_embedding,
        skill_embeddings=skill_embeddings,
        skill_names=industry_skills,
        index=faiss_index,
        top_k=user_request.top_k
    )
    
    return {"skill_gaps": gaps}

# ------------------------------------------------------------------
# Cleanup: close the Neo4j driver on shutdown
# ------------------------------------------------------------------
@app.on_event("shutdown")
def shutdown_event():
    neo4j_driver.close()