from flask import Flask, request, jsonify
from neo4j import GraphDatabase
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Set
import logging
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
CORS(app)

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

# Create a single global analyzer (you could set up multiple if needed)
analyzer = CareerPathAnalyzer(uri="bolt://localhost:7687", user="neo4j", password="priyanshi")

@app.route('/api/initialize', methods=['GET'])
def initialize():
    """
    Example endpoint that could be used by the React app to confirm
    the Flask server is running or perform any setup tasks.
    """
    return jsonify({"message": "System initialized"}), 200

@app.route('/api/analyze-skills', methods=['POST'])
def analyze_skills():
    """
    Endpoint that receives a list of skills and returns analysis
    or skill gaps based on the existing logic.
    """
    data = request.get_json()
    if not data or 'skills' not in data:
        return jsonify({"error": "No skills provided"}), 400

    try:
        result = analyzer.analyze_career_paths("test1")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error analyzing skills: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(debug=True, port=5000)
    finally:
        analyzer.close()