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

const MAX_VISIBLE_CARDS = 4;

const LearningPage = () => {
  const [startIndex, setStartIndex] = useState(0);

  const [flippedStates, setFlippedStates] = useState(
    Array(flashcardsData.length).fill(false)
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
              <div
                className={`card-inner ${isFlipped ? "flipped" : ""}`}
              >
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
    </div>
  );
};

export default LearningPage;