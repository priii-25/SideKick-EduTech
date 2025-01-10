import React, { useEffect, useState } from 'react';
import './skillJobMatching.css';

const SkillJobMatching = () => {
  const [hexagons, setHexagons] = useState([]);
  
  useEffect(() => {
    const initialHexagons = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      size: 40 + Math.random() * 40,
      animationDuration: 15 + Math.random() * 20,
      delay: Math.random() * -20,
      opacity: 0.1 + Math.random() * 0.2
    }));
    setHexagons(initialHexagons);
  }, []);

  return (
    <div className="background-wrapper">
      {}
      {hexagons.map((hexagon) => (
        <div
          key={hexagon.id}
          className="hexagon"
          style={{
            left: `${hexagon.left}%`,
            width: `${hexagon.size}px`,
            height: `${hexagon.size * 0.866}px`,
            animationDuration: `${hexagon.animationDuration}s`,
            animationDelay: `${hexagon.delay}s`,
            opacity: hexagon.opacity
          }}
        />
      ))}

      {}
      <div className="content-container">
        <h2>Skill-Job Matching and SWOT Analysis</h2>
        <p className="description">Analyze your skills and find jobs that fit you perfectly.</p>

        <div className="swot-grid">
          <div className="swot-item strengths">
            <h3>Strengths🏆</h3>
            <p>Highlight your key abilities, relevant experiences, and certifications related to your job goals.</p>
          </div>

          <div className="swot-item weaknesses">
            <h3>Weaknesses⚠️</h3>
            <p>Identify areas needing improvement, such as lack of certain technical skills or limited experience.</p>
          </div>

          <div className="swot-item opportunities">
            <h3>Opportunities💡</h3>
            <p>Explore emerging fields, training programs, and networking chances that can boost your career.</p>
          </div>

          <div className="swot-item threats">
            <h3>Threats😢</h3>
            <p>Understand market competition, economic changes, and skill-set gaps that might hinder your progress.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillJobMatching;