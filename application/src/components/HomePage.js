import React from 'react';
import './homePage.css'; 

const HomePage = () => {
  return (
    <div className="home-page">
      <nav className="navbar">
        <ul>
          <li><a href="/">HOME</a></li>
          <li><a href="/skill-job-matching">SKILL-JOB MATCHING</a></li>
          <li><a href="/profile">MY PROFILE</a></li>
          <li><a href="/learning">LEARNING</a></li>
        </ul>
      </nav>

      <header className="hero-section">
        <h1 className="hero-title">Welcome to SkillUp</h1>
        <p className="hero-subtitle">Your personalized learning path awaits!</p>
        <a href="/learning-path" className="btn">
          View Learning Path
        </a>
      </header>

      <section className="learning-path-section">
        <h2 className="section-heading">Personalized Learning Path: Data Scientist Roadmap (Beginner)</h2>

        {/* Phase 1 */}
        <div className="phase">
          <h3 className="phase-title">Phase 1: Strengthening Foundations (Months 1-3)</h3>
          <div className="milestone">
            <h4>Milestone 1: Solidify Python Fundamentals (Month 1)</h4>
            <p>Master Python syntax, data structures, and OOP. Use resources like Codecademy, DataCamp, or "Python Crash Course."</p>
          </div>
          <div className="milestone arrow"> 
            <h4>Milestone 2: Deepen Statistical Knowledge (Months 2-3)</h4>
            <p>Understand descriptive and inferential statistics. Try Khan Academy or "Practical Statistics for Data Scientists."</p>
          </div>
        </div>

        {/* Phase 2 */}
        <div className="phase">
          <h3 className="phase-title">Phase 2: Core Machine Learning (Months 4-9)</h3>
          <div className="milestone">
            <h4>Milestone 3: Linear Algebra Essentials (Month 4)</h4>
            <p>Focus on vectors, matrices, and linear transformations. Use resources like MIT OpenCourseware (Linear Algebra).</p>
          </div>
          <div className="milestone arrow">
            <h4>Milestone 4: Probability for Machine Learning (Month 5)</h4>
            <p>Dive into Bayes' theorem, random variables, and conditional probability. Reinforce statistical knowledge.</p>
          </div>
          <div className="milestone arrow">
            <h4>Milestone 5: Intro to Machine Learning Algorithms (Months 6-7)</h4>
            <p>Learn regression, classification, clustering, and model.eval metrics. Consider Coursera’s Stanford ML course.</p>
          </div>
          <div className="milestone arrow">
            <h4>Milestone 6: Deep Learning Fundamentals (Months 8-9)</h4>
            <p>Build basic deep learning models with TensorFlow. Explore the deeplearning.ai courses on Coursera.</p>
          </div>
        </div>

        {/* Phase 3 */}
        <div className="phase">
          <h3 className="phase-title">Phase 3: Building Projects & Expanding Skills (Months 10-12)</h3>
          <div className="milestone">
            <h4>Milestone 7: Data Science Projects (Months 10-11)</h4>
            <p>Apply your skills on real-world datasets. Consider Kaggle competitions and building a project portfolio.</p>
          </div>
          <div className="milestone arrow">
            <h4>Milestone 8: Develop Soft Skills & Networking (Ongoing)</h4>
            <p>Improve communication, join DS communities, and present your projects for feedback.</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;