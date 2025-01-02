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
    "Learn Python libraries such as pandas, NumPy, Matplotlib, and scikit-learn for data manipulation, analysis, and visualization.",
    "Master R for statistical computing and visualization using libraries like ggplot2 and dplyr.",
    "Understand SQL for querying databases and data extraction.",
    "Familiarize yourself with version control systems like Git and collaborative platforms like GitHub.",
    "Deep dive into probability, distributions, and Bayes' theorem for modeling and inference.",
    "Study linear algebra topics like vectors, matrices, and eigenvalues for machine learning foundations.",
    "Focus on statistical methods, hypothesis testing, and regression analysis for data interpretation.",
    "Learn calculus concepts such as differentiation and integration relevant to optimization in machine learning.",
    "Understand supervised learning techniques, including linear regression, logistic regression, and decision trees.",
    "Learn unsupervised learning techniques like clustering (K-means, DBSCAN) and dimensionality reduction (PCA, t-SNE).",
    "Explore ensemble methods, including Random Forest, Gradient Boosting, and XGBoost.",
    "Study model evaluation metrics like precision, recall, F1 score, and ROC-AUC.",
    "Master neural networks, convolutional neural networks (CNNs), and recurrent neural networks (RNNs).",
    "Learn frameworks like TensorFlow, PyTorch, and Keras for deep learning model development.",
    "Understand advanced topics such as transformers, attention mechanisms, and transfer learning using models like BERT and GPT.",
    "Explore big data tools such as Apache Hadoop, Spark, and Hive for distributed data processing.",
    "Learn cloud computing platforms like AWS, Azure, and Google Cloud for scalable data science workflows.",
    "Understand containerization with Docker and orchestration with Kubernetes for deploying data science solutions.",
    "Learn ETL (Extract, Transform, Load) processes and tools like Apache Airflow and Talend.",
    "Understand database management systems, including relational databases (PostgreSQL, MySQL) and NoSQL databases (MongoDB, Cassandra).",
    "Familiarize with data lakes and warehouses such as Snowflake, Redshift, and Databricks.",
    "Use Tableau or Power BI for interactive data visualization and dashboard creation.",
    "Learn advanced plotting techniques with Python libraries like seaborn, plotly, and bokeh.",
    "Practice storytelling with data to effectively communicate insights.",
    "Understand domain-specific applications such as healthcare analytics, finance modeling, and e-commerce optimization.",
    "Work on real-world projects like building recommendation systems, sentiment analysis, and predictive analytics models.",
    "Participate in data science competitions on Kaggle or contribute to open-source projects.",
    "Develop presentation skills to explain complex analyses to non-technical stakeholders.",
    "Understand data ethics, including fairness, accountability, and compliance with regulations like GDPR.",
    "Learn project management methodologies like CRISP-DM and agile for structuring data science projects.",
    "Dive into reinforcement learning for decision-making in dynamic environments.",
    "Study graph analytics and graph neural networks for social network analysis.",
    "Learn MLOps practices for deploying, monitoring, and maintaining machine learning models in production.",
    "Explore AutoML tools like H2O.ai, Google AutoML, and DataRobot for automating model building."
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
                template="""Based on the following retrieved context, generate a detailed and personalized roadmap.

Use MAJORLY the information provided in the context below to construct the roadmap.
If the context does not fully address the user's goal, provide guidance accordingly related and around the context ONLY. If nothing is present relavnt to the context and goal, provide a general roadmap and acknowledge the limitation.
Context: {context}

User Goal: {goal}
Current Capabilities: {capabilities}
Experience Level: {experience}

Please provide a detailed roadmap with specific milestones, resources, and timelines.

Roadmap:""",
                input_variables=["context", "goal", "capabilities", "experience"]
            )
            query = f"{goal} {capabilities} {experience}"
            docs = self.vectorstore.similarity_search(query, k=6)
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