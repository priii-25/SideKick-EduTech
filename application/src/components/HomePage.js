import React, { useState, useEffect } from 'react';
import './homePage.css';
import ReactMarkdown from 'react-markdown'; 

const HomePage = () => {
  const [activePhase, setActivePhase] = useState(1);
  const [roadmapData, setRoadmapData] = useState(null);
  const [phases, setPhases] = useState([]);

  const parseRoadmapContent = (markdownContent) => {
    const phaseRegex = /\*\*Phase \d+:[^*]+\*\*/g;
    const phases = markdownContent.match(phaseRegex).map((phase) => {
      const phaseNumber = phase.match(/Phase (\d+)/)[1];
      const phaseTitle = phase.match(/Phase \d+: ([^*]+)/)[1].trim();
      
      const milestoneStartIndex = markdownContent.indexOf(phase);
      const nextPhaseIndex = markdownContent.indexOf(`**Phase ${parseInt(phaseNumber) + 1}`, milestoneStartIndex);
      const phaseContent = markdownContent.slice(
        milestoneStartIndex,
        nextPhaseIndex === -1 ? undefined : nextPhaseIndex
      );
      
      const milestones = phaseContent
        .match(/\* ([^*\n]+)/g)
        ?.map(m => m.replace('* ', '').trim())
        .filter(Boolean) || [];

      return {
        number: parseInt(phaseNumber),
        title: phaseTitle,
        milestones,
        duration: phase.match(/\((\d+-\d+ weeks)\)/)?.[1] || '',
        skills: phaseContent.match(/\*\*Skills:\*\* ([^*\n]+)/)?.[1] || '',
      };
    });

    return phases;
  };

  useEffect(() => {
    fetch('http://127.0.0.1:8000/roadmap/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        goal: "Data Scientist",
        capabilities: "Intermediate understanding of Python, basic machine learning concepts",
        experience: "Beginner"
      })
    })
      .then(response => response.text())
      .then(data => {
        setRoadmapData(data);
        const parsedPhases = parseRoadmapContent(data);
        setPhases(parsedPhases);
      })
      .catch(error => console.error('Error fetching roadmap:', error));
  }, []);

  const scrollToContent = () => {
    const contentSection = document.querySelector('.section-header');
    contentSection.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="homepage">
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-content">
            <div className="logo">
              <span className="logo-text">SkillUp</span>
            </div>
            <div className="nav-links">
              {['Home', 'Skill-Job Matching', 'Profile', 'Learning'].map((item) => (
                <a
                  key={item}
                  href={`/${item.toLowerCase().replace(' ', '-')}`}
                  className="nav-link"
                >
                  {item}
                </a>
              ))}
            </div>
          </div>
        </div>
      </nav>

      <header className="hero">
        <h1 className="hero-title fade-in">
          Welcome to SideKick
        </h1>
        <h1>
          Your Trusted Companion in Learning and Growth!
        </h1>
        <p className="hero-subtitle fade-in">
          Your personalized journey to becoming a Data Scientist starts here
        </p>
        <button className="hero-button" onClick={scrollToContent}>
          Start Your Journey
        </button>
      </header>

      <main className="main-content">
        <div className="section-header">
          <h2 className="section-title">
            Data Scientist Roadmap (Beginner)
          </h2>
          <p className="section-description">
            Follow this carefully curated learning path to build a strong foundation in data science
          </p>
        </div>

        <div className="phases-grid">
          {phases.map((phase) => (
            <div
              key={phase.number}
              className={`phase-card ${activePhase === phase.number ? 'active' : ''}`}
              onClick={() => setActivePhase(phase.number)}
            >
              <div className="phase-content">
                <div className="phase-header">
                  <div className="phase-icon">
                    <span className="icon">
                      {phase.number === 1 ? '📚' : phase.number === 2 ? '🏆' : '🔬'}
                    </span>
                  </div>
                  <h3 className="phase-title">
                    Phase {phase.number}: {phase.title}
                  </h3>
                  <div className="phase-duration">{phase.duration}</div>
                </div>
                
                <div className="milestones">
                  {phase.number === activePhase && (
                    <div className="milestone-container fade-in">
                      <div className="skills">
                        <strong>Skills:</strong> {phase.skills}
                      </div>
                      {phase.milestones.map((milestone, index) => (
                        <div key={index} className="milestone">
                          <div className="milestone-dot"></div>
                          <div className="milestone-content">
                            <p className="milestone-description">
                              {milestone}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default HomePage;