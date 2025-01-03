from langchain.llms.base import LLM
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field
import traceback
from langchain.embeddings.base import Embeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import google.generativeai as genai
import torch
from transformers import AutoTokenizer, AutoModel
import os
import pickle

class HFEmbeddingWrapper(Embeddings):
    def __init__(self, model_name="distilbert-base-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        embeddings = []
        for text in texts:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
            embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
            embeddings.append(embedding.tolist())
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
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
def load_or_create_faiss(documents, faiss_index_file):
    '''if os.path.exists(faiss_index_file):
        print("Loading existing FAISS index...")
        with open(faiss_index_file, "rb") as f:
            vectorstore = pickle.load(f)
    else:'''
    print("Creating new FAISS index...")
    document_objects = [Document(page_content=doc) for doc in documents]
    vectorstore = FAISS.from_documents(document_objects, embedding_model)
    with open(faiss_index_file, "wb") as f:
        pickle.dump(vectorstore, f)
    return vectorstore

faiss_index_file = "offline_faiss_index.pkl"
vectorstore = load_or_create_faiss(documents, faiss_index_file)
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""Use the following context to answer the question. If you cannot answer based on the context, say "I don't have enough information."

Context: {context}

Question: {question}

Answer:"""
)

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

genai.configure(api_key="") 
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
llm_wrapper = GeminiLLMWrapper(model=gemini_model)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm_wrapper,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(
        search_kwargs={
            "k": 3, 
            "fetch_k": 5,
            "score_threshold": 0.5 
        }
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
    """Generate flashcards based on the given topic using the FAISS index."""
    try:
        flashcard_prompt = f"""Based on the available context, create {num_cards} detailed flashcards about {topic}.
        For each flashcard:
        1. Create a clear, specific question
        2. Provide a comprehensive answer
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
    """Generate a multiple-choice quiz based on the given topic."""
    try:
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

def display_flashcards(flashcards):
    """Display flashcards in a formatted way."""
    print("\n=== Flashcards ===\n")
    for i, card in enumerate(flashcards, 1):
        print(f"Flashcard #{i}")
        print(f"Question: {card.get('question', 'N/A')}")
        print(f"Answer: {card.get('answer', 'N/A')}")
        print("-" * 50)

def display_quiz(quiz):
    """Display quiz in a formatted way."""
    print("\n=== Quiz ===\n")
    for i, question in enumerate(quiz, 1):
        print(f"Question #{i}")
        print(f"Q: {question.get('question', 'N/A')}")
        print("\nOptions:")
        for option in question.get('options', []):
            print(option)
        print(f"\nCorrect Answer: {question.get('correct_answer', 'N/A')}")
        if 'explanation' in question:
            print(f"Explanation: {question['explanation']}")
        print("-" * 50)
'''
test_questions = [
    "What is machine learning?",
    "How do machine learning algorithms work?",
    "What is the difference between machine learning and deep learning?",
    "What are some applications of machine learning?"
]

if __name__ == "__main__":
    try:
        print("Testing QA System with Multiple Questions:\n")
        for question in test_questions:
            print("-" * 80)
            print(ask_question(question))
            print("-" * 80 + "\n")
    except Exception as e:
        print(f"System error: {str(e)}")

'''
if __name__ == "__main__":
    topics = [
        "Machine Learning",
        "Deep Learning",
        "Neural Networks",
        "Supervised Learning"
    ]

    for topic in topics:
        print(f"\n{'='*20} Studying {topic} {'='*20}")
        
        print(f"\nFlashcards for {topic}:")
        flashcards = generate_flashcards(topic, num_cards=3)
        display_flashcards(flashcards)
        
        print(f"\nQuiz for {topic}:")
        quiz = generate_quiz(topic, num_questions=2)
        display_quiz(quiz)
        
        print("="*60 + "\n")