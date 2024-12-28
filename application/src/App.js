import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage';
import SkillJobMatching from './components/SkillJobMatching';
import Profile from './components/Profile';
import LearningPath from './components/LearningPath';
import LearningPage from './components/LearningPage';
import Signup from './components/Signup';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/skill-job-matching" element={<SkillJobMatching />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/learning-path" element={<LearningPath />} />
          <Route path="/learning" element={<LearningPage />} />
          <Route path="/signup" element={<Signup />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
