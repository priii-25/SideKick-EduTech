import React, { useState, useEffect } from "react";
import "./LearningPage.css";

const MAX_VISIBLE_CARDS = 4;

const LearningPage = () => {
  const [flashcardsData, setFlashcardsData] = useState([]);
  const [quizData, setQuizData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [startIndex, setStartIndex] = useState(0);
  const [flippedStates, setFlippedStates] = useState([]);
  const [selectedOptions, setSelectedOptions] = useState([]);
  const [showExplanation, setShowExplanation] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        const [flashcardsResponse, quizResponse] = await Promise.all([
          fetch('http://localhost:8000/flashcards', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            mode: 'cors', 
            body: JSON.stringify({
              topic: "Machine Learning",
              num_cards: 6
            })
          }),
          fetch('http://localhost:8000/quiz', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            mode: 'cors', 
            body: JSON.stringify({
              topic: "Machine Learning",
              num_questions: 2
            })
          })
        ]);    
        const checkResponse = async (response, endpoint) => {
          if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(
              `${endpoint} failed: ${response.status} ${response.statusText}` +
              (errorData ? ` - ${errorData.detail}` : '')
            );
          }
          return response.json();
        };

        const [flashcardsResult, quizResult] = await Promise.all([
          checkResponse(flashcardsResponse, 'Flashcards'),
          checkResponse(quizResponse, 'Quiz')
        ]);

        const formattedFlashcards = flashcardsResult.map(card => ({
          id: card.id,
          question: card.question,
          answer: card.answer
        }));

        const formattedQuiz = quizResult.map(question => ({
          id: question.id,
          question: question.question,
          options: question.options,
          correctAnswer: question.options.findIndex(option => 
            option.startsWith(`${question.correct_answer})`)
          ),
          explanation: question.explanation
        }));

        setFlashcardsData(formattedFlashcards);
        setQuizData(formattedQuiz);
        setFlippedStates(Array(formattedFlashcards.length).fill(false));
        setSelectedOptions(Array(formattedQuiz.length).fill(null));
        setShowExplanation(Array(formattedQuiz.length).fill(false));
        
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);
  const visibleCardIndexes = [];
  for (let i = 0; i < MAX_VISIBLE_CARDS; i++) {
    visibleCardIndexes.push((startIndex + i) % (flashcardsData.length || 1));
  }

  const handleNext = () => {
    setStartIndex((prev) => (prev + 1) % flashcardsData.length);
    setFlippedStates(Array(flashcardsData.length).fill(false));
  };

  const handlePrev = () => {
    setStartIndex(
      (prev) => (prev - 1 + flashcardsData.length) % flashcardsData.length
    );
    setFlippedStates(Array(flashcardsData.length).fill(false));
  };

  const handleFlip = (cardIndex) => {
    setFlippedStates((prev) =>
      prev.map((val, i) => (i === cardIndex ? !val : false))
    );
  };

  const handleOptionChange = (questionIndex, optionIndex) => {
    setSelectedOptions((prev) =>
      prev.map((val, idx) => (idx === questionIndex ? optionIndex : val))
    );
  };

  const handleCheckAnswer = (questionIndex) => {
    setShowExplanation((prev) =>
      prev.map((val, idx) => (idx === questionIndex ? true : val))
    );
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="carousel-container">
      <h1>Learning Page</h1>

      {flashcardsData.length > 0 && (
        <>
          <div className="cards-row">
            {visibleCardIndexes.map((cardIdx) => {
              const card = flashcardsData[cardIdx];
              const isFlipped = flippedStates[cardIdx];
              return (
                <div
                  key={card.id}
                  className="card-container"
                  onClick={() => handleFlip(cardIdx)}
                >
                  <div className={`card-inner ${isFlipped ? "flipped" : ""}`}>
                    <div className="card-front">
                      <h3>Q: {card.question}</h3>
                    </div>
                    <div className="card-back">
                      <h3>A: {card.answer}</h3>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="nav-buttons">
            <button onClick={handlePrev}>Previous</button>
            <button onClick={handleNext}>Next</button>
          </div>
        </>
      )}

      {quizData.length > 0 && (
        <div className="quiz-section">
          <h2>Quiz</h2>
          {quizData.map((q, questionIndex) => (
            <div key={q.id} className="quiz-question">
              <h3>{q.question}</h3>
              <ul>
                {q.options.map((option, optIdx) => (
                  <li key={optIdx}>
                    <label>
                      <input
                        type="radio"
                        name={`question-${q.id}`}
                        value={optIdx}
                        checked={selectedOptions[questionIndex] === optIdx}
                        onChange={() => handleOptionChange(questionIndex, optIdx)}
                      />
                      {option}
                    </label>
                  </li>
                ))}
              </ul>
              <button onClick={() => handleCheckAnswer(questionIndex)}>
                Check Answer
              </button>
              {showExplanation[questionIndex] && (
                <div
                  className={
                    selectedOptions[questionIndex] === q.correctAnswer
                      ? "correct-answer"
                      : "incorrect-answer"
                  }
                >
                  {selectedOptions[questionIndex] === q.correctAnswer ? (
                    <p>Correct!</p>
                  ) : (
                    <p>Incorrect. The correct answer is: {q.options[q.correctAnswer]}</p>
                  )}
                  <p>{q.explanation}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LearningPage;