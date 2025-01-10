// SkillJobMatching.jsx
import React, { useEffect, useState } from 'react';
import './skillJobMatching.css';

const SkillJobMatching = () => {
  const [hexagons, setHexagons] = useState([]);
  const [swotData, setSwotData] = useState({
    strengths: [],
    weaknesses: [],
    opportunities: [],
    threats: []
  });

  useEffect(() => {
    // Initialize floating hexagons
    const initialHexagons = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      size: 40 + Math.random() * 40,
      animationDuration: 15 + Math.random() * 20,
      delay: Math.random() * -20,
      opacity: 0.1 + Math.random() * 0.2
    }));
    setHexagons(initialHexagons);

    fetch('http://localhost:5000/swot-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cv_path: 'test.pdf',
        industry_skills: '- Machine Learning\n- Data Visualization'
      })
    })
      .then(response => response.json())
      .then(data => {
        /*
           object structure 
          
          setSwotData({
            strengths: data.strengths,
            weaknesses: data.weaknesses,
            opportunities: data.opportunities,
            threats: data.threats
          });
        */

        const lines = data.swot.split('\n').map(line => line.trim());
        let strengths = [], weaknesses = [], opportunities = [], threats = [];
        let currentSection = null;

        lines.forEach(line => {
          if (line.startsWith('Strengths:')) currentSection = 'strengths';
          else if (line.startsWith('Weaknesses:')) currentSection = 'weaknesses';
          else if (line.startsWith('Opportunities:')) currentSection = 'opportunities';
          else if (line.startsWith('Threats:')) currentSection = 'threats';
          else if (line.startsWith('-') && currentSection !== null) {
            if (currentSection === 'strengths') strengths.push(line.replace('- ', ''));
            else if (currentSection === 'weaknesses') weaknesses.push(line.replace('- ', ''));
            else if (currentSection === 'opportunities') opportunities.push(line.replace('- ', ''));
            else if (currentSection === 'threats') threats.push(line.replace('- ', ''));
          }
        });

        setSwotData({
          strengths,
          weaknesses,
          opportunities,
          threats
        });
      })
      .catch(error => {
        console.error('Error fetching SWOT data:', error);
      });
  }, []);

  return (
    <div className="background-wrapper">
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

      <div className="content-container">
        <h2>Skill-Job Matching and SWOT Analysis</h2>
        <p className="description">Analyze your skills and find jobs that fit you perfectly.</p>

        <div className="swot-grid">
          <div className="swot-item strengths">
            <h3>Strengths🏆</h3>
            {swotData.strengths.map((item, idx) => (
              <p key={idx}>{item}</p>
            ))}
          </div>

          <div className="swot-item weaknesses">
            <h3>Weaknesses⚠️</h3>
            {swotData.weaknesses.map((item, idx) => (
              <p key={idx}>{item}</p>
            ))}
          </div>

          <div className="swot-item opportunities">
            <h3>Opportunities💡</h3>
            {swotData.opportunities.map((item, idx) => (
              <p key={idx}>{item}</p>
            ))}
          </div>

          <div className="swot-item threats">
            <h3>Threats😢</h3>
            {swotData.threats.map((item, idx) => (
              <p key={idx}>{item}</p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillJobMatching;