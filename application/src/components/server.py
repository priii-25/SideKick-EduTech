from typing import List, Dict, Set
from fastapi import FastAPI, Body, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified Skill Gap and SWOT Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["OPTIONS", "POST"],
    allow_headers=["Content-Type"]
)

sentence_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.2,
)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "priyanshi"))

class UserSkills(BaseModel):
    skills: List[str]
    top_k: int = 5

class SWOTRequest(BaseModel):
    cv_path: str
    industry_skills: str

def initialize_faiss(index_dim):
    index = faiss.IndexFlatIP(index_dim)
    return index

def vectorize_data(data, model):
    return model.encode(data, convert_to_tensor=False)

def populate_faiss_index(index, vectors):
    if len(vectors) == 0:
        return
    index.add(np.array(vectors, dtype=np.float32))

def retrieve_skill_requirements():
    query = """
    MATCH (s:Skill)-[:REQUIRED_FOR]->(j:Job)
    RETURN DISTINCT s.name AS skill
    """
    with neo4j_driver.session(database="jobsskills") as session:
        results = session.run(query)
        return [record['skill'] for record in results]

def find_skill_gaps(user_embedding, skill_names, index, top_k=5):
    D, I = index.search(user_embedding, top_k)
    gaps = [(skill_names[i], float(D[0][idx])) for idx, i in enumerate(I[0])]
    return gaps

def load_cv(file_path: str) -> str:
    try:
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)

        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        return ' '.join([doc.page_content for doc in texts])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading CV: {str(e)}")

def extract_profile_info(cv_text: str) -> str:
    profile_prompt = PromptTemplate(
        template="""Extract key information from the CV below and format it as a structured profile:
        CV Content: {cv_text}

        Format the output as:
        Name:
        Position:
        Skills:
        Experience:
        Education:
        Career Aspirations:""",
        input_variables=["cv_text"]
    )
    try:
        chain = profile_prompt | llm
        result = chain.invoke({"cv_text": cv_text})
        return result.content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting profile: {str(e)}")

def perform_swot_analysis(user_profile, industry_skills):
    swot_prompt = PromptTemplate(
        template="""Based on the user profile and industry skill demands, perform a SWOT analysis.

        User Profile: {user_profile}

        Industry Skill Demands: {industry_skills}

        Format your response as:

        Strengths:
        - (strength point 1)
        - (strength point 2)

        Weaknesses:
        - (weakness point 1)
        - (weakness point 2)

        Opportunities:
        - (opportunity point 1)
        - (opportunity point 2)

        Threats:
        - (threat point 1)
        - (threat point 2)""",
        input_variables=["user_profile", "industry_skills"]
    )
    try:
        chain = swot_prompt | llm
        result = chain.invoke({"user_profile": user_profile, "industry_skills": industry_skills})
        return result.content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error performing SWOT analysis: {str(e)}")

industry_skills = retrieve_skill_requirements()
if len(industry_skills) > 0:
    skill_embeddings = vectorize_data(industry_skills, sentence_model)
    skill_dim = skill_embeddings[0].shape[0]
    faiss_index = initialize_faiss(skill_dim)
    populate_faiss_index(faiss_index, skill_embeddings)
else:
    skill_embeddings = []
    faiss_index = None

@app.post("/skill-gaps")
def get_skill_gaps(user_request: UserSkills = Body(...)):
    if not faiss_index or len(skill_embeddings) == 0:
        return {"skill_gaps": []}

    user_vector = vectorize_data(user_request.skills, sentence_model)
    user_embedding = np.mean(user_vector, axis=0, keepdims=True).astype(np.float32)
    gaps = find_skill_gaps(user_embedding, industry_skills, faiss_index, user_request.top_k)
    return {"skill_gaps": gaps}

@app.post("/swot-analysis")
def api_swot_analysis(swot_request: SWOTRequest):
    cv_text = load_cv(swot_request.cv_path)
    user_profile = extract_profile_info(cv_text)
    swot_result = perform_swot_analysis(user_profile, swot_request.industry_skills)
    return {"swot": swot_result}

class CareerPathAnalyzer:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def close(self):
        self.driver.close()

    def analyze_career_paths(self, user_name: str, top_professions: int = 3) -> Dict:
        """Analyze possible career paths based on user's current skills."""
        user_skills = self._get_user_skills(user_name)
        if not user_skills:
            return {"error": "No skills found for user"}

        user_domains = self._get_domains_for_skills(user_skills)
        professions_data = self._get_all_professions_data()

        profession_matches = []
        for prof_name, prof_data in professions_data.items():
            match_score = self._calculate_profession_match(
                user_skills,
                user_domains,
                prof_data['required_skills'],
                prof_data['domains']
            )
            profession_matches.append((prof_name, match_score, prof_data))

        profession_matches.sort(key=lambda x: x[1], reverse=True)

        analysis = {
            "user_skills": list(user_skills),
            "user_domains": list(user_domains),
            "career_paths": []
        }

        for prof_name, match_score, prof_data in profession_matches[:top_professions]:
            missing_skills = set(prof_data['required_skills']) - set(user_skills)
            matching_skills = set(prof_data['required_skills']) & set(user_skills)
            path_analysis = {
                "profession": prof_name,
                "match_score": round(match_score * 100, 2),
                "matching_skills": list(matching_skills),
                "missing_skills": list(missing_skills),
                "missing_skills_by_domain": self._categorize_skills_by_domain(missing_skills),
                "related_professions": prof_data['related_professions']
            }
            analysis["career_paths"].append(path_analysis)

        return analysis

    def _get_user_skills(self, user_name: str) -> Set[str]:
        with self.driver.session(database="jobsskills") as session:
            query = """
                MATCH (u:User {name: $user_name})-[:HAS_SKILL]->(s:Skill)
                RETURN collect(s.name) AS skills
            """
            result = session.run(query, user_name=user_name)
            record = result.single()
            if record and record["skills"]:
                return set(record["skills"])
            return set()

    def _get_domains_for_skills(self, skills: Set[str]) -> Set[str]:
        if not skills:
            return set()
        with self.driver.session(database="jobsskills") as session:
            query = """
                MATCH (s:Skill)<-[:CONTAINS_SKILL]-(d:Domain)
                WHERE s.name IN $skills
                RETURN collect(DISTINCT d.name) AS domains
            """
            result = session.run(query, skills=list(skills))
            record = result.single()
            if record and record["domains"]:
                return set(record["domains"])
            return set()

    def _get_all_professions_data(self) -> Dict:
        with self.driver.session(database="jobsskills") as session:
            query = """
                MATCH (p:Profession)
                OPTIONAL MATCH (p)-[:REQUIRES_SKILL]->(s:Skill)
                OPTIONAL MATCH (p)-[:REQUIRES_DOMAIN]->(d:Domain)
                OPTIONAL MATCH (p)-[:RELATED_TO]->(rp:Profession)
                RETURN 
                    p.name AS profession,
                    collect(DISTINCT s.name) AS required_skills,
                    collect(DISTINCT d.name) AS domains,
                    collect(DISTINCT rp.name) AS related_professions
            """
            result = session.run(query)
            professions_data = {}
            for record in result:
                professions_data[record["profession"]] = {
                    "required_skills": record["required_skills"],
                    "domains": record["domains"],
                    "related_professions": record["related_professions"],
                }
            return professions_data

    def _calculate_profession_match(self, 
                                    user_skills: Set[str], 
                                    user_domains: Set[str],
                                    required_skills: List[str], 
                                    profession_domains: List[str]) -> float:
        if not required_skills: 
            skill_match = 0
        else:
            skill_match = len(set(required_skills) & user_skills) / len(required_skills)

        if profession_domains:
            domain_match = len(set(profession_domains) & user_domains) / len(profession_domains)
        else:
            domain_match = 0

        return 0.7 * skill_match + 0.3 * domain_match

    def _categorize_skills_by_domain(self, skills: Set[str]) -> Dict[str, List[str]]:
        if not skills:
            return {}
        with self.driver.session(database="jobsskills") as session:
            query = """
                MATCH (s:Skill)<-[:CONTAINS_SKILL]-(d:Domain)
                WHERE s.name IN $skills
                RETURN d.name AS domain, collect(s.name) AS domain_skills
            """
            result = session.run(query, skills=list(skills))
            categorized = {}
            for record in result:
                categorized[record["domain"]] = record["domain_skills"]
            
            all_categorized = set().union(*categorized.values()) if categorized else set()
            uncategorized = skills - all_categorized
            if uncategorized:
                categorized["Other"] = list(uncategorized)
            
            return categorized

analyzer = CareerPathAnalyzer(uri="bolt://localhost:7687", user="neo4j", password="priyanshi")

@app.get("/initialize")
def initialize():
    """
    Example endpoint that could be used by the React app to confirm
    the FastAPI server is running or perform any setup tasks.
    """
    return {"message": "System initialized"}

@app.post("/analyze-skills")
async def analyze_skills(request: Request):
    """
    Endpoint that receives a list of skills and returns analysis
    or skill gaps based on the existing logic.
    """
    data = await request.json()
    if not data or 'skills' not in data:
        raise HTTPException(status_code=400, detail="No skills provided")

    try:
        result = analyzer.analyze_career_paths("test1")
        return result
    except Exception as e:
        logger.error(f"Error analyzing skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
def shutdown_event():
    analyzer.close()
    neo4j_driver.close()