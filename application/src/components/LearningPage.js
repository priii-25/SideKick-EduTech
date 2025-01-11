import React, { useState } from "react";
import "./LearningPage.css";

const flashcardsData = [
  { id: 1, question: "Question 1", answer: "Answer 1" },
  { id: 2, question: "Question 2", answer: "Answer 2" },
  { id: 3, question: "Question 3", answer: "Answer 3" },
  { id: 4, question: "Question 4", answer: "Answer 4" },
  { id: 5, question: "Question 5", answer: "Answer 5" },
  { id: 6, question: "Question 6", answer: "Answer 6" }
];

const quizData = [
  {
    id: 1,
    question: "Which of the following best describes the core goal of supervised machine learning?",
    options: [
      "A) To identify patterns and structures in unlabeled data without any predefined outcomes.",
      "B) To allow the algorithm to learn and improve its performance over time without human intervention.",
      "C) To train a model to predict outcomes or make decisions based on labeled input data.",
      "D) To cluster data points into groups based on their similarity."
    ],
    correctAnswer: 2,
    explanation: "Supervised learning uses labeled datasets, meaning each data point is tagged with the correct answer. The algorithm learns to map inputs to outputs based on these labeled examples, enabling it to predict outcomes for new, unseen data. Options A describes unsupervised learning, B describes aspects of both supervised and unsupervised learning (especially reinforcement learning), and D describes clustering, a type of unsupervised learning."
  },
  {
    id: 2,
    question: "In the context of machine learning model evaluation, what does the term 'bias' refer to?",
    options: [
      "A) The model's ability to generalize well to unseen data.",
      "B) The difference between the model's predictions and the actual values.",
      "C) A systematic error in the model that is consistent across different datasets.",
      "D) The randomness in the model's predictions due to stochastic processes."
    ],
    correctAnswer: 2,
    explanation: "Bias in a machine learning model refers to a systematic error that consistently affects the model's predictions. It's a measure of how far off the model's average prediction is from the actual value, often caused by flaws in the training data or the model's design itself. Option B describes error, Option A describes generalization, and Option D describes variance."
  }
];

const MAX_VISIBLE_CARDS = 4;

const LearningPage = () => {
  const [startIndex, setStartIndex] = useState(0);
  const [flippedStates, setFlippedStates] = useState(
    Array(flashcardsData.length).fill(false)
  );

  const [selectedOptions, setSelectedOptions] = useState(
    Array(quizData.length).fill(null)
  );
  const [showExplanation, setShowExplanation] = useState(
    Array(quizData.length).fill(false)
  );

  const visibleCardIndexes = [];
  for (let i = 0; i < MAX_VISIBLE_CARDS; i++) {
    visibleCardIndexes.push((startIndex + i) % flashcardsData.length);
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

  return (
    <div className="carousel-container">
      <h1>Learning Page</h1>

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

      {/* Quiz section */}
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
                  <p>You selected the correct answer!</p>
                ) : (
                  <p>Incorrect. The correct answer is: {q.options[q.correctAnswer]}</p>
                )}
                <p>{q.explanation}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default LearningPage;