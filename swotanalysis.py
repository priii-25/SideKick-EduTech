import os
import faiss
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.2,
)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_cv(file_path: str) -> str:
    """Load CV from PDF or text file."""
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path)
    
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    texts = text_splitter.split_documents(documents)
    
    return ' '.join([doc.page_content for doc in texts])

def extract_profile_info(cv_text: str) -> str:
    """Extract relevant profile information from CV."""
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
    
    chain = profile_prompt | llm
    result = chain.invoke({"cv_text": cv_text})
    return result.content

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

def perform_swot_analysis(user_profile, industry_skills):
    """Perform SWOT analysis based on user profile and industry skills."""
    swot_prompt = PromptTemplate(
        template="""Based on the user profile and industry skill demands, perform a SWOT analysis.

User Profile: {user_profile}

Industry Skill Demands: {industry_skills}

Please provide a detailed SWOT analysis with the following format:

Strengths:
- (List strengths)

Weaknesses:
- (List weaknesses)

Opportunities:
- (List opportunities)

Threats:
- (List threats)

SWOT Analysis:""",
        input_variables=["user_profile", "industry_skills"]
    )

    chain = swot_prompt | llm
    result = chain.invoke({
        "user_profile": user_profile,
        "industry_skills": industry_skills
    })

    return result.content

def main():
    cv_path = "test.pdf"  
    cv_text = load_cv(cv_path)
    user_profile = extract_profile_info(cv_text)

    industry_skills = """
    - Advanced Machine Learning
    - Deep Learning
    - Big Data Technologies
    - Cloud Computing
    - Data Visualization
    """

    swot_analysis = perform_swot_analysis(user_profile, industry_skills)
    print("SWOT Analysis:\n", swot_analysis)

if __name__ == "__main__":
    main()