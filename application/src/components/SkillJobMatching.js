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
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      const initialHexagons = Array.from({ length: 20 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        size: 40 + Math.random() * 40,
        animationDuration: 15 + Math.random() * 20,
        delay: Math.random() * -20,
        opacity: 0.1 + Math.random() * 0.2
      }));
      setHexagons(initialHexagons);
    }, 100);

    fetch('http://localhost:5000/swot-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cv_path: 'test.pdf',
        industry_skills: '- Machine Learning\n- Data Visualization'
      })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('Raw SWOT data:', data);

        if (!data.swot) {
          throw new Error('SWOT data is missing in the response');
        }

        // Remove any markdown formatting
        const cleanText = data.swot.replace(/\*\*/g, '').replace(/\*/g, '-');
        const lines = cleanText.split('\n').map(line => line.trim()).filter(line => line);
        
        let strengths = [], weaknesses = [], opportunities = [], threats = [];
        let currentSection = null;

        lines.forEach(line => {
          const lowerLine = line.toLowerCase();
          
          if (lowerLine.includes('strengths:')) {
            currentSection = 'strengths';
          } else if (lowerLine.includes('weaknesses:')) {
            currentSection = 'weaknesses';
          } else if (lowerLine.includes('opportunities:')) {
            currentSection = 'opportunities';
          } else if (lowerLine.includes('threats:')) {
            currentSection = 'threats';
          } else if ((line.startsWith('-') || line.startsWith('•')) && currentSection) {
            const item = line.replace(/^[-•]\s*/, '').trim();
            if (item) {
              switch (currentSection) {
                case 'strengths':
                  strengths.push(item);
                  break;
                case 'weaknesses':
                  weaknesses.push(item);
                  break;
                case 'opportunities':
                  opportunities.push(item);
                  break;
                case 'threats':
                  threats.push(item);
                  break;
                default:
                  console.warn(`Unexpected section: ${currentSection}`);
                  break;
              }
            }
          }
        });

        console.log('Parsed SWOT data:', { strengths, weaknesses, opportunities, threats });

        setSwotData({
          strengths,
          weaknesses,
          opportunities,
          threats
        });
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching SWOT data:', error);
        setError(error.message);
        setLoading(false);
      });

    return () => clearTimeout(timer);
  }, []);

  if (error) {
    return (
      <div className="background-wrapper">
        <div className="content-container">
          <h2>Error Loading SWOT Analysis</h2>
          <p className="error-message">{error}</p>
        </div>
      </div>
    );
  }

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
            opacity: hexagon.opacity,
            '--opacity': hexagon.opacity
          }}
        />
      ))}

      <div className="content-container">
        <h2>Skill-Job Matching and SWOT Analysis</h2>
        <p className="description">Analyze your skills and find jobs that fit you perfectly.</p>

        <div className="swot-grid">
          <div className="swot-item strengths">
            <h3>Strengths🏆</h3>
            {loading ? (
              <p>Loading strengths...</p>
            ) : swotData.strengths.length > 0 ? (
              swotData.strengths.map((item, idx) => (
                <p key={idx}>{item}</p>
              ))
            ) : (
              <p>No strengths found</p>
            )}
          </div>

          <div className="swot-item weaknesses">
            <h3>Weaknesses⚠️</h3>
            {loading ? (
              <p>Loading weaknesses...</p>
            ) : swotData.weaknesses.length > 0 ? (
              swotData.weaknesses.map((item, idx) => (
                <p key={idx}>{item}</p>
              ))
            ) : (
              <p>No weaknesses found</p>
            )}
          </div>

          <div className="swot-item opportunities">
            <h3>Opportunities💡</h3>
            {loading ? (
              <p>Loading opportunities...</p>
            ) : swotData.opportunities.length > 0 ? (
              swotData.opportunities.map((item, idx) => (
                <p key={idx}>{item}</p>
              ))
            ) : (
              <p>No opportunities found</p>
            )}
          </div>

          <div className="swot-item threats">
            <h3>Threats😢</h3>
            {loading ? (
              <p>Loading threats...</p>
            ) : swotData.threats.length > 0 ? (
              swotData.threats.map((item, idx) => (
                <p key={idx}>{item}</p>
              ))
            ) : (
              <p>No threats found</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillJobMatching;