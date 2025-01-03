import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
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
        self.memory = ConversationBufferMemory()
        self._load_prompts()

    def _initialize_llm(self, model_name: str, temperature: float) -> ChatGoogleGenerativeAI:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
        )

    def _load_prompts(self):
        self.question_prompt = PromptTemplate(
            template="""Given this candidate profile:
{profile}

Generate {num_questions} technical questions across different difficulty levels (basic, intermediate, advanced).
Consider their background in: {skills}

Return in JSON format:
{{"questions": [
    {{"text": "question", "criteria": "criteria", "difficulty": "basic|intermediate|advanced"}}
]}}""",
            input_variables=["profile", "num_questions", "skills"]
        )

    def generate_questions(self, profile: Dict, num_questions: int = 10) -> List[Question]:
        try:
            result = self.llm.invoke(
                self.question_prompt.format(
                    profile=json.dumps(profile),
                    num_questions=num_questions,
                    skills=", ".join(profile.get("skills", []))
                )
            )
            questions_data = json.loads(result.content)["questions"]
            return [
                Question(
                    text=q["text"],
                    criteria=q["criteria"],
                    difficulty=QuestionDifficulty(q["difficulty"])
                ) for q in questions_data
            ]
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return self._fallback_questions()

    def evaluate_response(self, response: str, criteria: str) -> Dict:
        eval_prompt = PromptTemplate(
            template="""Evaluate this response:
Response: {response}
Criteria: {criteria}

Return JSON:
{{"score": 0-100, "feedback": "detailed feedback", "strengths": [], "areas_for_improvement": []}}""",
            input_variables=["response", "criteria"]
        )
        
        try:
            result = self.llm.invoke(eval_prompt.format(response=response, criteria=criteria))
            return json.loads(result.content)
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return self._fallback_evaluation()

    def _fallback_questions(self) -> List[Question]:
        return [
            Question(
                text="Explain a challenging project you worked on",
                criteria="Problem-solving and technical depth",
                difficulty=QuestionDifficulty.INTERMEDIATE
            ),
            Question(
                text="How do you keep up with industry trends?",
                criteria="Learning ability and industry awareness",
                difficulty=QuestionDifficulty.BASIC
            )
        ]

    def _fallback_evaluation(self) -> Dict:
        return {
            "score": 70,
            "feedback": "Moderate response, needs more detail",
            "strengths": ["Basic understanding demonstrated"],
            "areas_for_improvement": ["Add more specific examples"]
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
            
            answer = input("Your answer: ")
            evaluation = self.scorer.evaluate_response(answer, question.criteria)
            
            self.responses.append(Response(question, answer, evaluation))
            final_scores.append(evaluation["score"])
            
            print(f"\nFeedback: {evaluation['feedback']}")
            print(f"Score: {evaluation['score']}/100")

        return self._generate_final_report(final_scores)

    def _generate_final_report(self, scores: List[float]) -> Dict:
        avg_score = sum(scores) / len(scores)
        return {
            "overall_score": round(avg_score, 2),
            "total_questions": len(self.responses),
            "performance_summary": self._get_performance_summary(avg_score),
            "responses": [(r.question.text, r.evaluation) for r in self.responses]
        }

    def _get_performance_summary(self, score: float) -> str:
        if score >= 90: return "Excellent candidate"
        elif score >= 80: return "Strong candidate"
        elif score >= 70: return "Competent candidate"
        else: return "Needs improvement"

def main():
    try:
        load_dotenv()
        scorer = LLMEmployabilityScorer()
        interviewer = EmployabilityInterviewer(scorer)
        
        profile = {
            "name": "John Doe",
            "current_role": "Data Scientist",
            "experience": "3 years",
            "skills": ["Python", "Machine Learning", "Data Analysis"],
            "education": "Master's in Computer Science"
        }
        
        final_report = interviewer.conduct_interview(profile)
        print("\nFinal Report:", json.dumps(final_report, indent=2))
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    main()