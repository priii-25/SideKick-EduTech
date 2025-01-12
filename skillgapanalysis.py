from neo4j import GraphDatabase
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        # Get user's domain expertise
        user_domains = self._get_domains_for_skills(user_skills)
        
        # Get all professions and their requirements
        professions_data = self._get_all_professions_data()
        
        # Calculate profession matches
        profession_matches = []
        for prof_name, prof_data in professions_data.items():
            match_score = self._calculate_profession_match(
                user_skills,
                user_domains,
                prof_data['required_skills'],
                prof_data['domains']
            )
            profession_matches.append((prof_name, match_score, prof_data))
        
        # Sort by match score
        profession_matches.sort(key=lambda x: x[1], reverse=True)
        
        # Prepare detailed analysis
        analysis = {
            "user_skills": list(user_skills),
            "user_domains": list(user_domains),
            "career_paths": []
        }
        
        # Analyze top matching professions
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
        """Get user's current skills."""
        with self.driver.session(database="jobsskills") as session:
            query = """
                MATCH (u:User {name: $user_name})-[:HAS_SKILL]->(s:Skill)
                RETURN collect(s.name) AS skills
            """
            result = session.run(query, user_name=user_name)
            return set(result.single()["skills"])

    def _get_domains_for_skills(self, skills: Set[str]) -> Set[str]:
        """Get domains associated with given skills."""
        with self.driver.session(database="jobsskills") as session:
            query = """
                MATCH (s:Skill)<-[:CONTAINS_SKILL]-(d:Domain)
                WHERE s.name IN $skills
                RETURN collect(DISTINCT d.name) AS domains
            """
            result = session.run(query, skills=list(skills))
            return set(result.single()["domains"])

    def _get_all_professions_data(self) -> Dict:
        """Get comprehensive data for all professions."""
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
            return {
                record["profession"]: {
                    "required_skills": record["required_skills"],
                    "domains": record["domains"],
                    "related_professions": record["related_professions"]
                }
                for record in result
            }

    def _calculate_profession_match(self, 
                                  user_skills: Set[str], 
                                  user_domains: Set[str],
                                  required_skills: List[str], 
                                  profession_domains: List[str]) -> float:
        """Calculate how well user matches a profession."""
        # Calculate skill match
        skill_match = len(set(required_skills) & user_skills) / len(required_skills)
        
        # Calculate domain match
        domain_match = len(set(profession_domains) & user_domains) / len(profession_domains) if profession_domains else 0
        
        # Weighted average (skills count more than domains)
        return 0.7 * skill_match + 0.3 * domain_match

    def _categorize_skills_by_domain(self, skills: Set[str]) -> Dict[str, List[str]]:
        """Categorize skills by their domains."""
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
            
            # Add uncategorized skills
            all_categorized = set().union(*categorized.values()) if categorized else set()
            uncategorized = skills - all_categorized
            if uncategorized:
                categorized["Other"] = list(uncategorized)
            
            return categorized

if __name__ == "__main__":
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "priyanshi"
    
    analyzer = CareerPathAnalyzer(uri, user, password)
    
    try:
        # Analyze career paths for test1
        analysis = analyzer.analyze_career_paths("test1")
        
        print("\n=== Career Path Analysis ===")
        print(f"\nCurrent Skills: {', '.join(analysis['user_skills'])}")
        print(f"Domains: {', '.join(analysis['user_domains'])}")
        
        print("\nTop Career Paths:")
        for path in analysis['career_paths']:
            print(f"\n{path['profession']}:")
            print(f"Match Score: {path['match_score']}%")
            print(f"Matching Skills: {', '.join(path['matching_skills'])}")
            print("\nMissing Skills by Domain:")
            for domain, skills in path['missing_skills_by_domain'].items():
                print(f"  {domain}: {', '.join(skills)}")
            if path['related_professions']:
                print(f"Related Professions: {', '.join(path['related_professions'])}")
            print("-" * 50)
    
    finally:
        analyzer.close()