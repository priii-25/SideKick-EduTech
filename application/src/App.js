import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage';
import SkillJobMatching from './components/SkillJobMatching';
import Profile from './components/Profile';
import LearningPage from './components/LearningPage';
import Signup from './components/Signup';
import Chatbot from './components/chatbot';
import SkillGapAnalyzer from './components/SkillGapAnalyzer';
import GraphVisualization from './components/GraphVisualization';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/home" element={<HomePage />} />
          <Route path="/skill-job-matching" element={<SkillJobMatching />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/learning" element={<LearningPage />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/GraphVisualization" element={<GraphVisualization />} />
          <Route path="/Skill" element={<SkillGapAnalyzer />} />
        </Routes>
        <Chatbot />
      </div>
    </Router>
  );
}

export default App;
