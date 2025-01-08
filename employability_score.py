import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import json
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionDifficulty(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class Question:
    text: str
    criteria: str
    difficulty: QuestionDifficulty

@dataclass
class Response:
    question: Question
    answer: str
    evaluation: Optional[Dict] = None

class BaseLLMScorer(ABC):
    @abstractmethod
    def generate_questions(self, profile: Dict) -> List[Question]:
        pass
    
    @abstractmethod
    def evaluate_response(self, response: str, criteria: str) -> Dict:
        pass

class LLMEmployabilityScorer(BaseLLMScorer):
    def __init__(self, model_name: str = "gemini-1.5-pro", temperature: float = 0.2):
        self.llm = self._initialize_llm(model_name, temperature)
        self._load_prompts()

    def _initialize_llm(self, model_name: str, temperature: float) -> ChatGoogleGenerativeAI:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            convert_system_message_to_human=True
        )

    def _load_prompts(self):
        self.question_prompt = PromptTemplate(
            template="""You are an expert technical interviewer. Based on this candidate profile:
{profile}

Generate exactly {num_questions} technical questions that thoroughly assess their skills.
Distribute questions across these levels:
- 4 basic questions
- 3 intermediate questions
- 3 advanced questions

Focus on their background in: {skills}

Format your response EXACTLY as follows (maintain proper JSON syntax):
{{
  "questions": [
    {{
      "text": "<question text>",
      "criteria": "<evaluation criteria>",
      "difficulty": "<basic/intermediate/advanced>"
    }}
  ]
}}""",
            input_variables=["profile", "num_questions", "skills"]
        )

        self.evaluation_prompt = PromptTemplate(
            template="""Evaluate this technical interview response:
Question: {question}
Response: {response}
Evaluation Criteria: {criteria}

Provide your evaluation in the following JSON format EXACTLY (maintain proper JSON syntax):
{{
  "score": <number between 0-100>,
  "feedback": "<detailed constructive feedback>",
  "strengths": [
    "<strength 1>",
    "<strength 2>"
  ],
  "areas_for_improvement": [
    "<area 1>",
    "<area 2>"
  ]
}}""",
            input_variables=["question", "response", "criteria"]
        )

    def _parse_llm_response(self, response_text: str, default_value: Dict) -> Dict:
        """Safely parse LLM response with better error handling"""
        try:
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return default_value

    def generate_questions(self, profile: Dict, num_questions: int = 10) -> List[Question]:
        try:
            result = self.llm.invoke(
                self.question_prompt.format(
                    profile=json.dumps(profile),
                    num_questions=num_questions,
                    skills=", ".join(profile.get("skills", []))
                )
            )
            
            questions_data = self._parse_llm_response(
                result.content,
                {"questions": self._get_default_questions()}
            )["questions"]

            questions = [
                Question(
                    text=q["text"],
                    criteria=q["criteria"],
                    difficulty=QuestionDifficulty(q["difficulty"])
                ) for q in questions_data
            ]

            while len(questions) < num_questions:
                questions.extend(self._get_default_questions())
            return questions[:num_questions]

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return self._get_default_questions()

    def evaluate_response(self, question: str, response: str, criteria: str) -> Dict:
        try:
            result = self.llm.invoke(
                self.evaluation_prompt.format(
                    question=question,
                    response=response,
                    criteria=criteria
                )
            )
            
            evaluation = self._parse_llm_response(
                result.content,
                self._get_default_evaluation(response)
            )
            
            evaluation["score"] = max(0, min(100, evaluation.get("score", 70)))
            return evaluation

        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return self._get_default_evaluation(response)

    def _get_default_questions(self) -> List[Dict]:
        return [
            {
                "text": "Explain your most challenging technical project in detail.",
                "criteria": "Technical depth, problem-solving, and project management",
                "difficulty": "intermediate"
            },
            {
                "text": "How do you stay updated with the latest industry trends and technologies?",
                "criteria": "Learning ability, industry awareness, and professional development",
                "difficulty": "basic"
            },
            {
                "text": "Describe a time when you had to debug a complex technical issue.",
                "criteria": "Problem-solving, debugging skills, and technical knowledge",
                "difficulty": "advanced"
            }
        ]

    def _get_default_evaluation(self, response: str) -> Dict:
        words = len(response.split())
        if words < 10:
            score = 30
            detail_level = "minimal"
        elif words < 30:
            score = 50
            detail_level = "partial"
        else:
            score = 70
            detail_level = "adequate"

        return {
            "score": score,
            "feedback": f"Response shows {detail_level} detail and engagement with the question.",
            "strengths": ["Attempted to answer the question"],
            "areas_for_improvement": [
                "Provide more specific examples and details",
                "Demonstrate deeper technical understanding",
                "Structure response more clearly"
            ]
        }

class EmployabilityInterviewer:
    def __init__(self, scorer: BaseLLMScorer):
        self.scorer = scorer
        self.responses: List[Response] = []

    def conduct_interview(self, profile: Dict, num_questions: int = 10) -> Dict:
        questions = self.scorer.generate_questions(profile, num_questions)
        final_scores = []

        for i, question in enumerate(questions, 1):
            logger.info(f"\nQuestion {i}/{num_questions} ({question.difficulty.value})")
            print(f"\nQ{i}: {question.text}")
            print(f"Difficulty: {question.difficulty.value}")
            print(f"Evaluation Criteria: {question.criteria}")
            
            answer = input("\nYour answer: ").strip()
            while not answer:  
                print("Please provide an answer to continue.")
                answer = input("Your answer: ").strip()
            
            evaluation = self.scorer.evaluate_response(question.text, answer, question.criteria)
            
            self.responses.append(Response(question, answer, evaluation))
            final_scores.append(evaluation["score"])
            
            print("\nEvaluation:")
            print(f"Score: {evaluation['score']}/100")
            print(f"Feedback: {evaluation['feedback']}")
            print("\nStrengths:")
            for strength in evaluation['strengths']:
                print(f"- {strength}")
            print("\nAreas for Improvement:")
            for area in evaluation['areas_for_improvement']:
                print(f"- {area}")

        return self._generate_final_report(final_scores)

    def _generate_final_report(self, scores: List[float]) -> Dict:
        avg_score = sum(scores) / len(scores)
        difficulty_scores = self._calculate_difficulty_scores()
        
        return {
            "overall_score": round(avg_score, 2),
            "total_questions": len(self.responses),
            "performance_summary": self._get_performance_summary(avg_score),
            "difficulty_breakdown": difficulty_scores,
            "responses": [
                {
                    "question": r.question.text,
                    "difficulty": r.question.difficulty.value,
                    "score": r.evaluation["score"],
                    "feedback": r.evaluation["feedback"]
                } for r in self.responses
            ]
        }

    def _calculate_difficulty_scores(self) -> Dict:
        difficulty_scores = {d.value: [] for d in QuestionDifficulty}
        for response in self.responses:
            difficulty_scores[response.question.difficulty.value].append(
                response.evaluation["score"]
            )
        
        return {
            difficulty: {
                "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
                "num_questions": len(scores)
            }
            for difficulty, scores in difficulty_scores.items()
        }

    def _get_performance_summary(self, score: float) -> str:
        if score >= 90: return "Outstanding candidate with exceptional technical skills"
        elif score >= 80: return "Strong candidate showing solid technical competence"
        elif score >= 70: return "Competent candidate with good technical foundation"
        elif score >= 60: return "Shows potential but needs some improvement"
        else: return "Significant improvement needed in technical skills"

def main():
    try:
        load_dotenv()
        scorer = LLMEmployabilityScorer()
        interviewer = EmployabilityInterviewer(scorer)
        
        profile = {
            "name": input("Enter candidate name: "),
            "current_role": input("Enter current role: "),
            "experience": input("Enter years of experience: "),
            "skills": input("Enter skills (comma-separated): ").split(","),
            "education": input("Enter education: ")
        }
        
        print("\nStarting technical interview assessment...")
        final_report = interviewer.conduct_interview(profile, num_questions=10)
        
        print("\nFinal Report:")
        print(json.dumps(final_report, indent=2))
        
        filename = f"interview_report_{profile['name'].replace(' ', '_').lower()}.json"
        with open(filename, 'w') as f:
            json.dumps(final_report, f, indent=2)
        print(f"\nReport saved to {filename}")
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    main()