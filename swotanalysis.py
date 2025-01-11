import os
import faiss
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["OPTIONS", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.2,
)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_cv(file_path: str) -> str:
    """Load CV from PDF or text file."""
    try:
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
    except Exception as e:
        print(f"Error loading CV: {str(e)}")
        return ""

def extract_profile_info(cv_text: str) -> str:
    """Extract key information from the user's CV."""
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
        print("Profile extraction result:", result.content)
        return result.content
    except Exception as e:
        print(f"Error extracting profile: {str(e)}")
        return ""

def perform_swot_analysis(user_profile, industry_skills):
    """Perform SWOT analysis based on user profile and industry demands."""
    swot_prompt = PromptTemplate(
        template="""Based on the user profile and industry skill demands, perform a SWOT analysis.

User Profile: {user_profile}

Industry Skill Demands: {industry_skills}

Format your response exactly like this, using simple dashes for bullets:

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
        result = chain.invoke({
            "user_profile": user_profile,
            "industry_skills": industry_skills
        })
        print("Raw SWOT Result:", result.content)
        return result.content
    except Exception as e:
        print(f"Error performing SWOT analysis: {str(e)}")
        return ""

@app.route('/swot-analysis', methods=['POST'])
def api_swot_analysis():
    try:
        data = request.get_json()
        cv_path = data.get("cv_path")
        industry_skills = data.get("industry_skills", "")

        if not cv_path:
            return jsonify({"error": "cv_path is required"}), 400

        cv_text = load_cv(cv_path)
        if not cv_text:
            return jsonify({"error": "Failed to load CV"}), 400

        user_profile = extract_profile_info(cv_text)
        if not user_profile:
            return jsonify({"error": "Failed to extract profile"}), 400

        swot_result = perform_swot_analysis(user_profile, industry_skills)
        if not swot_result:
            return jsonify({"error": "Failed to perform SWOT analysis"}), 400

        return jsonify({"swot": swot_result})
    
    except Exception as e:
        print(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)