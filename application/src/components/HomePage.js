import React, { useState } from 'react';
import './homePage.css';

const HomePage = () => {
  const [activePhase, setActivePhase] = useState(1);

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
          {[1, 2, 3].map((phase) => (
            <div
              key={phase}
              className={`phase-card ${activePhase === phase ? 'active' : ''}`}
              onClick={() => setActivePhase(phase)}
            >
              <div className="phase-content">
                <div className="phase-header">
                  <div className="phase-icon">
                    <span className="icon">
                      {phase === 1 ? '📚' : phase === 2 ? '🏆' : '👥'}
                    </span>
                  </div>
                  <h3 className="phase-title">
                    Phase {phase}: {phase === 1 ? 'Foundations' : phase === 2 ? 'Core ML' : 'Projects'}
                  </h3>
                </div>
                
                <div className="milestones">
                  {phase === activePhase && (
                    <div className="milestone-container fade-in">
                      {[1, 2].map((milestone) => (
                        <div key={milestone} className="milestone">
                          <div className="milestone-dot"></div>
                          <div className="milestone-content">
                            <h4 className="milestone-title">
                              Milestone {milestone}
                            </h4>
                            <p className="milestone-description">
                              {phase === 1 && milestone === 1 && "Master Python fundamentals including syntax, data structures, and OOP"}
                              {phase === 1 && milestone === 2 && "Deep dive into statistics and probability fundamentals"}
                              {phase === 2 && milestone === 1 && "Learn core machine learning algorithms and mathematics"}
                              {phase === 2 && milestone === 2 && "Build and train neural networks with TensorFlow"}
                              {phase === 3 && milestone === 1 && "Create real-world projects and build portfolio"}
                              {phase === 3 && milestone === 2 && "Network with the community and improve soft skills"}
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