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
        self.skill_hierarchy = {
            "foundational": {
                "programming": ["Python", "R", "SQL"],
                "mathematics": ["Statistics", "Linear Algebra", "Calculus"],
                "tools": ["Git", "Command Line"]
            },
            "intermediate": {
                "data_processing": ["Pandas", "NumPy", "Data Cleaning"],
                "visualization": ["Matplotlib", "Seaborn", "Tableau"],
                "ml_basics": ["Scikit-learn", "Model Evaluation", "Feature Engineering"]
            },
            "advanced": {
                "deep_learning": ["Neural Networks", "TensorFlow", "PyTorch"],
                "big_data": ["Spark", "Hadoop", "Cloud Computing"],
                "deployment": ["MLOps", "Docker", "API Development"]
            }
        }

    def load_or_create_faiss(self):
        documents = [
            "Learn Python libraries such as pandas, NumPy, Matplotlib, and scikit-learn for data manipulation, analysis, and visualization.",
            "Explore AutoML tools like H2O.ai, Google AutoML, and DataRobot for automating model building.",
            "Start with foundational programming skills in Python, focusing on data structures and algorithms.",
            "Build upon basic programming with intermediate data processing using pandas and NumPy.",
            "Progress to advanced topics like deep learning only after mastering core machine learning concepts.",
            "Develop mathematical foundations before moving to complex statistical modeling.",
            "Master data visualization tools progressively, starting from basic plots to interactive dashboards.",
            "Learn deployment technologies after gaining solid modeling experience."
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

    def determine_skill_level(self, capabilities: str) -> str:
        """Determine the starting skill level based on user capabilities."""
        capabilities_lower = capabilities.lower()
        if "expert" in capabilities_lower or "advanced" in capabilities_lower:
            return "advanced"
        elif "intermediate" in capabilities_lower or "experienced" in capabilities_lower:
            return "intermediate"
        return "foundational"

    def get_relevant_skills(self, skill_level: str) -> list:
        """Get relevant skills based on determined skill level."""
        skills = []
        levels = list(self.skill_hierarchy.keys())
        start_index = levels.index(skill_level)
        
        for level in levels[start_index:min(start_index + 2, len(levels))]:
            for category, category_skills in self.skill_hierarchy[level].items():
                skills.extend(category_skills)
        return skills

    def generate_roadmap(self, goal: str, capabilities: str, experience: str):
        try:
            skill_level = self.determine_skill_level(capabilities)
            relevant_skills = self.get_relevant_skills(skill_level)
            
            prompt_template = PromptTemplate(
                template="""Based on the following retrieved context and skill hierarchy, generate a detailed and personalized roadmap.

Context: {context}

User Goal: {goal}
Current Capabilities: {capabilities}
Experience Level: {experience}
Relevant Skills to Focus On: {relevant_skills}

Please provide a structured learning path that:
1. Follows a clear progression from foundational to advanced concepts
2. Groups related skills and technologies together
3. Provides specific milestones and prerequisites for each stage
4. Includes estimated timelines for each phase
5. Suggests specific resources or projects for practical application

Format the roadmap in clear phases, with each phase building upon the previous one.
Ensure concepts are introduced in a logical order based on dependencies.

Roadmap:""",
                input_variables=["context", "goal", "capabilities", "experience", "relevant_skills"]
            )
            
            query = f"{goal} {capabilities} {experience}"
            docs = self.vectorstore.similarity_search(query, k=6)
            context = "\n".join([doc.page_content for doc in docs])
            
            chain = prompt_template | self.llm
            result = chain.invoke({
                "context": context,
                "goal": goal,
                "capabilities": capabilities,
                "experience": experience,
                "relevant_skills": ", ".join(relevant_skills)
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