from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv
import os
import os
import pickle
import traceback
from datetime import datetime, timezone
from langchain.llms.base import LLM
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import google.generativeai as genai
import torch
from transformers import AutoTokenizer, AutoModel
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="ML Learning Assistant API",
    description="API for generating flashcards, quizzes, and answering questions about Machine Learning",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)
class QuestionRequest(BaseModel):
    question: str

class FlashcardRequest(BaseModel):
    topic: str
    num_cards: Optional[int] = 5

class QuizRequest(BaseModel):
    topic: str
    num_questions: Optional[int] = 5

class Flashcard(BaseModel):
    question: str
    answer: str

class QuizOption(BaseModel):
    options: List[str]
    question: str
    correct_answer: str
    explanation: str

class HFEmbeddingWrapper(Embeddings):
    def __init__(self, model_name="distilbert-base-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
            embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
            embeddings.append(embedding.tolist())
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
        return embedding.tolist()

documents = [
    "Machine learning is a branch of artificial intelligence that enables computers to learn from data and improve their performance on specific tasks without being explicitly programmed.",
    "Machine learning algorithms work by analyzing large amounts of data to identify patterns and make predictions or decisions based on those patterns.",
    "Supervised learning is a type of machine learning where algorithms learn from labeled training data to make predictions on new, unseen data.",
    "Deep learning is a subset of machine learning using neural networks with multiple layers to process complex patterns in data.",
    "Neural networks are computing systems inspired by biological neural networks, consisting of interconnected nodes that process and transmit information.",
    "Common machine learning applications include image recognition, natural language processing, recommendation systems, and fraud detection.",
    "Machine learning models require training data to learn patterns and validation data to assess their performance.",
    "Feature extraction is an important step in machine learning where relevant information is selected from raw data.",
    "FAISS (Facebook AI Similarity Search) is a library developed by Facebook for efficient similarity search and clustering of dense vectors.",
    "LangChain is a framework for developing applications powered by language models, combining various tools and capabilities."
]

embedding_model = HFEmbeddingWrapper()
faiss_index_file = "offline_faiss_index.pkl"

def load_or_create_faiss(documents, faiss_index_file):
    try:
        if os.path.exists(faiss_index_file):
            print("Loading existing FAISS index...")
            with open(faiss_index_file, "rb") as f:
                try:
                    vectorstore = pickle.load(f)
                    return vectorstore
                except:
                    print("Error loading existing index, creating new one...")
                    os.remove(faiss_index_file)
                    
        print("Creating new FAISS index...")
        document_objects = [Document(page_content=doc) for doc in documents]
        vectorstore = FAISS.from_documents(document_objects, embedding_model)
        with open(faiss_index_file, "wb") as f:
            pickle.dump(vectorstore, f)
        return vectorstore
    except Exception as e:
        print(f"Error in load_or_create_faiss: {str(e)}")
        document_objects = [Document(page_content=doc) for doc in documents]
        vectorstore = FAISS.from_documents(document_objects, embedding_model)
        return vectorstore

class GeminiLLMWrapper(LLM, BaseModel):
    model: Any = Field(default=None)

    class Config:
        arbitrary_types_allowed = True

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        try:
            response = self.model.generate_content(prompt)
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts'):
                return ' '.join(part.text for part in response.parts)
            else:
                return str(response)
        except Exception as e:
            return f"Error generating response: {str(e)}"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": "gemini-1.5-flash"}

    @property
    def _llm_type(self) -> str:
        return "gemini"

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
llm_wrapper = GeminiLLMWrapper(model=gemini_model)
vectorstore = None

def create_qa_chain():
    global vectorstore
    if vectorstore is None:
        vectorstore = load_or_create_faiss(documents, faiss_index_file)
    
    return RetrievalQA.from_chain_type(
        llm=llm_wrapper,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_kwargs={"k": 3, "fetch_k": 5, "score_threshold": 0.5}
        ),
        return_source_documents=True,
        chain_type_kwargs={
            "prompt": PromptTemplate(
                input_variables=["context", "question"],
                template="""Use the following context to provide a comprehensive answer to the question. If the context doesn't contain enough information, you may use your general knowledge to supplement the answer, but indicate which parts are from the context and which are additional information.

Context: {context}

Question: {question}

Answer (be specific and detailed):"""
            )
        }
    )

def ask_question(question: str):
    try:
        qa_chain = create_qa_chain()
        result = qa_chain({"query": question})
        answer = result.get("result", "No answer generated")
        sources = result.get("source_documents", [])

        response = f"Question: {question}\n\n"
        response += f"Answer: {answer}\n"
        if sources:
            response += "\nRelevant Sources:\n"
            for i, doc in enumerate(sources, 1):
                response += f"{i}. {doc.page_content}\n"
                if hasattr(doc, 'metadata') and 'score' in doc.metadata:
                    response += f"   Similarity Score: {doc.metadata['score']:.3f}\n"
        return response
    except Exception as e:
        return f"Error processing question: {str(e)}\nTrace: {traceback.format_exc()}"

def generate_flashcards(topic: str, num_cards: int = 5):
    try:
        qa_chain = create_qa_chain()  
        
        flashcard_prompt = f"""Based on the available context, create {num_cards} detailed flashcards about {topic}.
        For each flashcard:
        1. Create a clear, specific question
        2. Provide a comprehensive answer within 50 words
        3. Use the following format exactly:
        CARD #number
        Q: (question)
        A: (detailed answer)
        ---
        """

        result = qa_chain({"query": flashcard_prompt})
        cards_text = result.get("result", "")

        flashcards = []
        current_card = {}

        for line in cards_text.split('\n'):
            line = line.strip()
            if line.startswith('CARD'):
                if current_card:
                    flashcards.append(current_card)
                current_card = {}
            elif line.startswith('Q:'):
                current_card['question'] = line[2:].strip()
            elif line.startswith('A:'):
                current_card['answer'] = line[2:].strip()

        if current_card:
            flashcards.append(current_card)

        return flashcards
    except Exception as e:
        print(f"Error generating flashcards: {str(e)}")
        return []

def generate_quiz(topic: str, num_questions: int = 5):
    try:
        qa_chain = create_qa_chain()  
        
        quiz_prompt = f"""Create a {num_questions}-question multiple-choice quiz about {topic} using the following format:

        QUESTION #number
        Q: (detailed question)
        Options:
        A) (option 1)
        B) (option 2)
        C) (option 3)
        D) (option 4)
        Correct Answer: (letter)
        Explanation: (why this is the correct answer)
        ---

        Make each question test understanding of {topic} concepts.
        Ensure only one answer is correct.
        Include brief explanations for the correct answers.
        """

        result = qa_chain({"query": quiz_prompt})
        quiz_text = result.get("result", "")

        quiz = []
        current_question = {}

        for line in quiz_text.split('\n'):
            line = line.strip()
            if line.startswith('QUESTION'):
                if current_question:
                    quiz.append(current_question)
                current_question = {'options': []}
            elif line.startswith('Q:'):
                current_question['question'] = line[2:].strip()
            elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                current_question['options'].append(line)
            elif line.startswith('Correct Answer:'):
                current_question['correct_answer'] = line.replace('Correct Answer:', '').strip()
            elif line.startswith('Explanation:'):
                current_question['explanation'] = line.replace('Explanation:', '').strip()

        if current_question:
            quiz.append(current_question)

        return quiz
    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
        return []

@app.get("/")
async def root():
    return {
        "message": "Welcome to ML Learning Assistant API",
        "current_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

@app.post("/ask", response_model=Dict[str, str])
async def ask_question_endpoint(request: QuestionRequest):
    try:
        response = ask_question(request.question)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/flashcards", response_model=List[Flashcard])
async def create_flashcards(request: FlashcardRequest):
    try:
        flashcards = generate_flashcards(request.topic, request.num_cards)
        return flashcards
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quiz", response_model=List[QuizOption])
async def create_quiz(request: QuizRequest):
    try:
        quiz = generate_quiz(request.topic, request.num_questions)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.options("/flashcards")
async def create_flashcards(request: FlashcardRequest):
    try:
        flashcards = generate_flashcards(request.topic, request.num_cards)
        return flashcards
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.options("/quiz")
async def create_quiz(request: QuizRequest):
    try:
        quiz = generate_quiz(request.topic, request.num_questions)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    global vectorstore
    try:
        vectorstore = load_or_create_faiss(documents, faiss_index_file)
    except Exception as e:
        print(f"Error initializing FAISS index: {str(e)}")
        raise e

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)