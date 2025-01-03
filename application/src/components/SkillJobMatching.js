import React from 'react';
import './skillJobMatching.css';

const SkillJobMatching = () => {
  return (
    <div className="skill-job-matching-container">
      <h2>Skill-Job Matching and SWOT Analysis</h2>
      <p>Analyze your skills and find jobs that fit you perfectly.</p>

      <div className="swot-board">
        <div className="swot-item swot-strengths">
          <h3>Strengths</h3>
          <p>Highlight your key abilities, relevant experiences, and certifications related to your job goals.</p>
        </div>

        <div className="swot-item swot-weaknesses">
          <h3>Weaknesses</h3>
          <p>Identify areas needing improvement, such as lack of certain technical skills or limited experience.</p>
        </div>

        <div className="swot-item swot-opportunities">
          <h3>Opportunities</h3>
          <p>Explore emerging fields, training programs, and networking chances that can boost your career.</p>
        </div>

        <div className="swot-item swot-threats">
          <h3>Threats</h3>
          <p>Understand market competition, economic changes, and skill-set gaps that might hinder your progress.</p>
        </div>
      </div>
    </div>
  );
};

export default SkillJobMatching;