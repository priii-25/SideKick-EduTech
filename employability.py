import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import json
import logging
from abc import ABC, abstractmethod
import numpy as np

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

@dataclass
class InterviewMemory:
    past_responses: List[Response] = field(default_factory=list)
    candidate_strengths: List[str] = field(default_factory=list)
    candidate_weaknesses: List[str] = field(default_factory=list)
    interaction_history: List[Dict] = field(default_factory=list)
    strategy_adjustments: List[str] = field(default_factory=list)

class BaseLLMScorer(ABC):
    @abstractmethod
    def generate_questions(self, profile: Dict) -> List[Question]:
        pass
    
    @abstractmethod
    def evaluate_response(self, response: str, criteria: str) -> Dict:
        pass

class AgentLLMEmployabilityScorer(BaseLLMScorer):
    def __init__(self, model_name: str = "gemini-1.5-pro", temperature: float = 0.2):
        self.llm = self._initialize_llm(model_name, temperature)
        self._load_prompts()
        self.memory = InterviewMemory()
        self.difficulty_weights = {"basic": 0.3, "intermediate": 0.3, "advanced": 0.4}
        self.target_score_threshold = 75

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
Distribute questions based on these weights:
{weights}

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
            input_variables=["profile", "num_questions", "weights", "skills"]
        )

        self.evaluation_prompt = PromptTemplate(
            template="""Evaluate this technical interview response:
Question: {question}
Response: {response}
Evaluation Criteria: {criteria}
Previous Responses: {history}

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
            input_variables=["question", "response", "criteria", "history"]
        )

    def adapt_strategy(self, response: Response) -> None:
        current_difficulty = response.question.difficulty.value
        if response.evaluation["score"] > 85:
            self.difficulty_weights[current_difficulty] -= 0.1
            self._increase_harder_difficulties(current_difficulty)
        elif response.evaluation["score"] < 60:
            self.difficulty_weights[current_difficulty] += 0.1
            self._decrease_harder_difficulties(current_difficulty)
            
        self._normalize_weights()
        
        self.memory.strategy_adjustments.append(
            f"Adjusted weights after {current_difficulty} question: {self.difficulty_weights}"
        )

    def _normalize_weights(self):
        total = sum(self.difficulty_weights.values())
        self.difficulty_weights = {
            k: v/total for k, v in self.difficulty_weights.items()
        }

    def _increase_harder_difficulties(self, current_difficulty: str) -> None:
        difficulties = ["basic", "intermediate", "advanced"]
        current_idx = difficulties.index(current_difficulty)
        for diff in difficulties[current_idx + 1:]:
            self.difficulty_weights[diff] += 0.05

    def _decrease_harder_difficulties(self, current_difficulty: str) -> None:
        difficulties = ["basic", "intermediate", "advanced"]
        current_idx = difficulties.index(current_difficulty)
        for diff in difficulties[:current_idx]:
            self.difficulty_weights[diff] += 0.05

    def generate_questions(self, profile: Dict, num_questions: int = 10) -> List[Question]:
        try:
            result = self.llm.invoke(
                self.question_prompt.format(
                    profile=json.dumps(profile),
                    num_questions=num_questions,
                    weights=json.dumps(self.difficulty_weights),
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

            if self.memory.past_responses:
                performance_by_topic = self._analyze_topic_performance()
                questions = self._prioritize_questions(questions, performance_by_topic)

            while len(questions) < num_questions:
                questions.extend(self._get_default_questions())
            return questions[:num_questions]

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return self._get_default_questions()

    def evaluate_response(self, question: str, response: str, criteria: str) -> Dict:
        try:
            history_summary = self._summarize_history() if self.memory.interaction_history else "No previous interactions"
            
            result = self.llm.invoke(
                self.evaluation_prompt.format(
                    question=question,
                    response=response,
                    criteria=criteria,
                    history=history_summary
                )
            )
            
            evaluation = self._parse_llm_response(
                result.content,
                self._get_default_evaluation(response)
            )
            
            evaluation["score"] = max(0, min(100, evaluation.get("score", 70)))
            
            # Update memory
            self.memory.interaction_history.append({
                "question": question,
                "response": response,
                "evaluation": evaluation
            })
            
            if evaluation["score"] >= 80:
                self.memory.candidate_strengths.extend(evaluation["strengths"])
            if evaluation["score"] <= 60:
                self.memory.candidate_weaknesses.extend(evaluation["areas_for_improvement"])
            
            return evaluation

        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return self._get_default_evaluation(response)

    def _summarize_history(self) -> str:
        return json.dumps([{
            "question": h["question"],
            "score": h["evaluation"]["score"]
        } for h in self.memory.interaction_history[-3:]])  # Last 3 interactions

    def _parse_llm_response(self, response_text: str, default_value: Dict) -> Dict:
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

    def _analyze_topic_performance(self) -> Dict[str, float]:
        topic_scores = {}
        for interaction in self.memory.interaction_history:
            topics = self._extract_topics(interaction["question"])
            score = interaction["evaluation"]["score"]
            for topic in topics:
                if topic not in topic_scores:
                    topic_scores[topic] = []
                topic_scores[topic].append(score)
        
        return {
            topic: np.mean(scores) for topic, scores in topic_scores.items()
        }

    def _extract_topics(self, question: str) -> List[str]:
        prompt = f"Extract key technical topics from this question: {question}"
        result = self.llm.invoke(prompt)
        topics = result.content.split(",")
        return [t.strip().lower() for t in topics]

    def _prioritize_questions(self, questions: List[Question], 
                            topic_performance: Dict[str, float]) -> List[Question]:
        scored_questions = []
        for q in questions:
            topics = self._extract_topics(q.text)
            avg_topic_score = np.mean([
                topic_performance.get(t, 75) for t in topics
            ])
            priority_score = 100 - avg_topic_score
            scored_questions.append((priority_score, q))
            
        scored_questions.sort(reverse=True)
        return [q for _, q in scored_questions]

    def _get_default_questions(self) -> List[Dict]:
        return [
            {
                "text": "Explain your most challenging technical project in detail.",
                "criteria": "Technical depth, problem-solving, and project management",
                "difficulty": "intermediate"
            },
            {
                "text": "How do you stay updated with the latest industry trends?",
                "criteria": "Learning ability and professional development",
                "difficulty": "basic"
            },
            {
                "text": "Describe a complex technical issue you debugged.",
                "criteria": "Problem-solving and technical knowledge",
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
            "feedback": f"Response shows {detail_level} detail and engagement.",
            "strengths": ["Attempted to answer the question"],
            "areas_for_improvement": [
                "Provide more specific examples",
                "Demonstrate deeper technical understanding",
                "Structure response more clearly"
            ]
        }

class AgentEmployabilityInterviewer:
    def __init__(self, scorer: AgentLLMEmployabilityScorer):
        self.scorer = scorer
        self.responses: List[Response] = []
        self.target_score = 75
        self.max_questions = 15

    def conduct_interview(self, profile: Dict, num_questions: int = 10) -> Dict:
        questions_asked = 0
        running_score = 0
        
        while questions_asked < self.max_questions:
            remaining = min(3, self.max_questions - questions_asked)
            if remaining <= 0:
                break
                
            questions = self.scorer.generate_questions(profile, remaining)
            
            for question in questions:
                result = self._ask_question(question, questions_asked + 1)
                running_score = self._update_running_score(result)
                
                self.scorer.adapt_strategy(result)
                questions_asked += 1
                
                if running_score >= self.target_score and questions_asked >= 5:
                    logger.info("Target score achieved with sufficient questions")
                    return self._generate_final_report(
                        [r.evaluation["score"] for r in self.responses]
                    )
                    
        return self._generate_final_report([r.evaluation["score"] for r in self.responses])

    def _ask_question(self, question: Question, q_num: int) -> Response:
        logger.info(f"\nQuestion {q_num} ({question.difficulty.value})")
        print(f"\nQ{q_num}: {question.text}")
        print(f"Difficulty: {question.difficulty.value}")
        print(f"Evaluation Criteria: {question.criteria}")
        
        answer = input("\nYour answer: ").strip()
        while not answer:
            print("Please provide an answer to continue.")
            answer = input("Your answer: ").strip()
        
        evaluation = self.scorer.evaluate_response(question.text, answer, question.criteria)
        response = Response(question, answer, evaluation)
        self.responses.append(response)
        
        self._display_feedback(evaluation)
        return response

    def _update_running_score(self, response: Response) -> float:
        scores = [r.evaluation["score"] for r in self.responses]
        return np.mean(scores)

    def _display_feedback(self, evaluation: Dict) -> None:
        print(f"\nScore: {evaluation['score']}/100")
        print(f"Feedback: {evaluation['feedback']}")
        print("\nStrengths:")
        for strength in evaluation['strengths'][:2]:
            print(f"- {strength}")
        print("\nAreas for Improvement:")
        for area in evaluation['areas_for_improvement'][:2]:
            print(f"- {area}")

    def _generate_final_report(self, scores: List[float]) -> Dict:
        avg_score = sum(scores) / len(scores)
        difficulty_scores = self._calculate_difficulty_scores()
        
        return {
            "overall_score": round(avg_score, 2),
            "total_questions": len(self.responses),
            "performance_summary": self._get_performance_summary(avg_score),
            "difficulty_breakdown": difficulty_scores,
            "strategy_adaptations": self.scorer.memory.strategy_adjustments,
            "candidate_strengths": list(set(self.scorer.memory.candidate_strengths)),
            "candidate_weaknesses": list(set(self.scorer.memory.candidate_weaknesses)),
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
        scorer = AgentLLMEmployabilityScorer()
        interviewer = AgentEmployabilityInterviewer(scorer)
        
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
            json.dump(final_report, f, indent=2)
        print(f"\nReport saved to {filename}")
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    main()