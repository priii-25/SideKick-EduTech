from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI   
from langchain_huggingface import HuggingFaceEmbeddings
import pickle
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.2,
)

class RoadMap:
    def __init__(self, google_api_key: str, faiss_index: str = "roadmap_faiss_index.pkl"):
        self.faiss_index = faiss_index
        self.llm = llm
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = self.load_or_create_faiss()

    def load_or_create_faiss(self):
        documents = [
            "To become a data scientist, you need to learn Python, statistics, and machine learning.",
            "For web development, focus on HTML, CSS, JavaScript, and frameworks like React or Django.",
            "Cloud computing skills include AWS, Azure, and Docker.",
            "To master machine learning, study linear algebra, probability, and deep learning frameworks like TensorFlow.",
            "Soft skills like communication and teamwork are essential for all careers.",
        ]

        if os.path.exists(self.faiss_index):
            print("Loading Faiss Index")
            with open(self.faiss_index, "rb") as f:
                return pickle.load(f)
        else:
            print("Creating Faiss Index")
            document_object = [Document(page_content=doc) for doc in documents]
            vectorstore = FAISS.from_documents(document_object, self.embedding_model)
            with open(self.faiss_index, "wb") as f:
                pickle.dump(vectorstore, f)
            return vectorstore

    def generate_roadmap(self, goal: str, capabilities: str, experience: str):
        try:
            prompt_template = PromptTemplate(
                template="""Based on the following information and context, generate a detailed and personalized roadmap.

Context: {context}

User Goal: {goal}
Current Capabilities: {capabilities}
Experience Level: {experience}

Please provide a detailed roadmap with specific milestones, resources, and timelines.

Roadmap:""",
                input_variables=["context", "goal", "capabilities", "experience"]
            )
            query = f"{goal} {capabilities} {experience}"
            docs = self.vectorstore.similarity_search(query, k=3)
            context = "\n".join([doc.page_content for doc in docs])
            chain = prompt_template | self.llm
            result = chain.invoke({
                "context": context,
                "goal": goal,
                "capabilities": capabilities,
                "experience": experience
            })

            return result.content

        except Exception as e:
            return f"Error in making roadmap😢. Please try again later. Error: {e}"
if __name__ == "__main__":
    roadmap = RoadMap(os.getenv("GOOGLE_API_KEY"))
    user_goal = "Become a data scientist"
    user_capabilities = "I know Python basics and have some experience with statistics."
    user_experience = "Beginner"
    print("Generating roadmap...\n")
    roadmap_output = roadmap.generate_roadmap(
        goal=user_goal,
        capabilities=user_capabilities,
        experience=user_experience
    )
    print(roadmap_output)