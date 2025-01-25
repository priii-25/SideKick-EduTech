from neo4j import GraphDatabase
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SkillGapAnalyzer:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_domains_and_skills(self, domains):
        """Create domains and link them to their respective skills."""
        with self.driver.session(database="jobsskills") as session:
            for domain, skills in domains.items():
                session.execute_write(self._create_domain_skills, domain, skills)

    @staticmethod
    def _create_domain_skills(tx, domain, skills):
        """Create or merge domain nodes and their skills."""
        query = (
            "MERGE (d:Domain {name: $domain}) "
            "WITH d "
            "UNWIND $skills AS skill "
            "MERGE (s:Skill {name: skill}) "
            "MERGE (d)-[:CONTAINS_SKILL]->(s)"
        )
        tx.run(query, domain=domain, skills=skills)

    def add_profession_domains(self, profession, domains):
        """Link professions to relevant skill domains."""
        with self.driver.session(database="jobsskills") as session:
            session.execute_write(self._create_profession_domains, profession, domains)

    @staticmethod
    def _create_profession_domains(tx, profession, domains):
        """Associate a profession with required domains."""
        query = (
            "MERGE (p:Profession {name: $profession}) "
            "WITH p "
            "UNWIND $domains AS domain "
            "MATCH (d:Domain {name: domain}) "
            "MERGE (p)-[:REQUIRES_DOMAIN]->(d)"
        )
        tx.run(query, profession=profession, domains=domains)

    def add_profession_associations(self, profession, related_professions):
        """Link professions to related professions."""
        with self.driver.session(database="jobsskills") as session:
            session.execute_write(self._create_profession_associations, profession, related_professions)

    @staticmethod
    def _create_profession_associations(tx, profession, related_professions):
        """Associate a profession with related professions."""
        query = (
            "MERGE (p:Profession {name: $profession}) "
            "WITH p "
            "UNWIND $related_professions AS related_profession "
            "MERGE (r:Profession {name: related_profession}) "
            "MERGE (p)-[:RELATED_TO]->(r)"
        )
        tx.run(query, profession=profession, related_professions=related_professions)

    def add_profession_skills(self, profession, skills):
        """Link professions directly to required skills."""
        with self.driver.session(database="jobsskills") as session:
            session.execute_write(self._create_profession_skills, profession, skills)

    @staticmethod
    def _create_profession_skills(tx, profession, skills):
        """Associate a profession with required skills."""
        query = (
            "MERGE (p:Profession {name: $profession}) "
            "WITH p "
            "UNWIND $skills AS skill "
            "MERGE (s:Skill {name: skill}) "
            "MERGE (p)-[:REQUIRES_SKILL]->(s)"
        )
        tx.run(query, profession=profession, skills=skills)

    def add_user_skills(self, user_name, skills):
        """Create a user and link them to their skills."""
        with self.driver.session(database="jobsskills") as session:
            session.execute_write(self._create_user_skills, user_name, skills)

    @staticmethod
    def _create_user_skills(tx, user_name, skills):
        """Associate a user with their skills."""
        query = (
            "MERGE (u:User {name: $user_name}) "
            "WITH u "
            "UNWIND $skills AS skill "
            "MATCH (s:Skill {name: skill}) "
            "MERGE (u)-[:HAS_SKILL]->(s)"
        )
        tx.run(query, user_name=user_name, skills=skills)

    def get_profession_domains(self, profession):
        """Retrieve all domains required by a profession."""
        with self.driver.session(database="jobsskills") as session:
            result = session.execute_read(self._query_profession_domains, profession)
        return result

    @staticmethod
    def _query_profession_domains(tx, profession):
        """Query all domains linked to the specified profession."""
        query = (
            "MATCH (p:Profession {name: $profession})-[:REQUIRES_DOMAIN]->(d:Domain) "
            "RETURN d.name AS name"
        )
        records = tx.run(query, profession=profession)
        return [record["name"] for record in records]

    def get_user_skills(self, user_name):
        """Retrieve all skills of a specific user."""
        with self.driver.session(database="jobsskills") as session:
            user_skills = session.execute_read(self._query_user_skills, user_name)
        return user_skills

    @staticmethod
    def _query_user_skills(tx, user_name):
        """Query all skills associated with the specified user."""
        query = (
            "MATCH (u:User {name: $user_name})-[:HAS_SKILL]->(s:Skill) "
            "RETURN s.name AS name"
        )
        records = tx.run(query, user_name=user_name)
        return [record["name"] for record in records]

    def calculate_cosine_similarity(self, user_skills, profession_skills):
        """Generate a cosine similarity score between a user's skills and a profession's required skills."""
        all_skills = list(set(user_skills + profession_skills))
        user_vector = np.array([1 if skill in user_skills else 0 for skill in all_skills])
        profession_vector = np.array([1 if skill in profession_skills else 0 for skill in all_skills])
        similarity = cosine_similarity([user_vector], [profession_vector])
        return similarity[0][0]

    def find_closest_profession(self, user_name):
        """Find the closest profession for a user based on their skills."""
        user_skills = self.get_user_skills(user_name)
        professions = self.get_all_professions()
        max_similarity = 0
        closest_profession = None

        for profession in professions:
            profession_skills = self.get_profession_skills(profession)
            similarity = self.calculate_cosine_similarity(user_skills, profession_skills)
            if similarity > max_similarity:
                max_similarity = similarity
                closest_profession = profession

        print(f"Closest Profession: {closest_profession}")
        print(f"Cosine Similarity: {max_similarity}")
        return closest_profession, max_similarity

    def get_all_professions(self):
        """Retrieve all professions from the database."""
        with self.driver.session(database="jobsskills") as session:
            result = session.execute_read(self._query_all_professions)
        return result

    @staticmethod
    def _query_all_professions(tx):
        """Query all professions in the database."""
        query = "MATCH (p:Profession) RETURN p.name AS name"
        records = tx.run(query)
        return [record["name"] for record in records]

    def get_profession_skills(self, profession):
        """Retrieve all skills required for a profession."""
        with self.driver.session(database="jobsskills") as session:
            result = session.execute_read(self._query_profession_skills, profession)
        return result

    @staticmethod
    def _query_profession_skills(tx, profession):
        """Query all skills linked to the specified profession."""
        query = (
            "MATCH (p:Profession {name: $profession})-[:REQUIRES_SKILL]->(s:Skill) "
            "RETURN s.name AS name"
        )
        records = tx.run(query, profession=profession)
        return [record["name"] for record in records]

if __name__ == "__main__":
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "priyanshi"

    analyzer = SkillGapAnalyzer(uri, user, password)

    '''domains = {
        "Machine Learning": ["PyTorch", "TensorFlow", "Scikit-learn", "Keras"],
        "DevOps": ["Docker", "Kubernetes", "Terraform", "Jenkins"],
        "Web Development": ["HTML", "CSS", "JavaScript", "React", "Node.js"],
        "Mobile Development": ["Swift", "Kotlin", "Flutter", "React Native"]
    }

    # Add domains with their associated skills
    analyzer.add_domains_and_skills(domains)

    # Define professions and their required domains
    professions = {
        "Software Engineer": ["Web Development", "Machine Learning"],
        "Frontend Developer": ["Web Development"],
        "Backend Developer": ["Web Development"],
        "Full Stack Developer": ["Web Development"],
        "Data Scientist": ["Machine Learning"],
        "ML Engineer": ["Machine Learning"],
        "DevOps Engineer": ["DevOps"],
        "Mobile Developer": ["Mobile Development"],
        "QA Engineer": ["Web Development"],
        "Business Analyst": ["Web Development"],
        "Product Manager": ["Web Development"],
        "Project Manager": ["Web Development"],
        "UI/UX Designer": ["Web Development"],
        "System Administrator": ["DevOps"]
    }

    # Add professions and their domain dependencies
    for profession, required_domains in professions.items():
        analyzer.add_profession_domains(profession, required_domains)

    # Define associations between professions
    related_professions = {
        "Software Engineer": ["Frontend Developer", "Backend Developer", "Full Stack Developer"],
        "Data Scientist": ["ML Engineer"],
        "DevOps Engineer": ["System Administrator"],
        "Mobile Developer": ["Frontend Developer"],
        "Project Manager": ["Product Manager"],
    }

    for profession, related in related_professions.items():
        analyzer.add_profession_associations(profession, related)

    # Define profession-specific skills
    profession_skills = {
        "Software Engineer": ["Python", "Java", "C++", "System Design", "Algorithms"],
        "Frontend Developer": ["HTML", "CSS", "JavaScript", "React", "Vue.js"],
        "Backend Developer": ["Node.js", "Django", "Spring Boot", "Database Design", "Microservices"],
        "Full Stack Developer": ["React", "Node.js", "MongoDB", "REST API", "Docker"],
        "Data Scientist": ["Python", "Pandas", "Numpy", "Machine Learning", "Deep Learning"],
        "ML Engineer": ["TensorFlow", "PyTorch", "ML Deployment", "Feature Engineering", "Cloud ML"],
        "DevOps Engineer": ["Docker", "Kubernetes", "CI/CD", "Terraform", "AWS"],
        "Mobile Developer": ["Kotlin", "Swift", "Flutter", "React Native"],
        "QA Engineer": ["Selenium", "Jest", "Unit Testing", "Performance Testing"],
        "Business Analyst": ["SQL", "Power BI", "Tableau", "Excel"],
        "Product Manager": ["Market Research", "Roadmap Planning", "Agile Development"],
        "Project Manager": ["Scrum", "JIRA", "Agile Methodology"],
        "UI/UX Designer": ["Figma", "Adobe XD", "Wireframing", "User Research"],
        "System Administrator": ["Linux", "Windows Server", "Network Configuration"]
    }

    for profession, skills in profession_skills.items():
        analyzer.add_profession_skills(profession, skills)'''

    user_name = "test1"
    user_skills = ["TensorFlow", "Docker", "React", "Kotlin"]

    analyzer.add_user_skills(user_name, user_skills)
    closest_profession, similarity_score = analyzer.find_closest_profession("test1")
    print(f"closest profession: {closest_profession} with similarity {similarity_score}")
    analyzer.close()