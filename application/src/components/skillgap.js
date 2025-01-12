import React, { useEffect, useState } from 'react';
import axios from 'axios';

function Skill() {
  const [skillGaps, setSkillGaps] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:5000/api/skill-gaps')
      .then(response => {
        setSkillGaps(response.data);
      })
      .catch(error => {
        console.error('Error fetching skill gaps:', error);
      });
  }, []);

  return (
    <div style={{ margin: '2rem' }}>
      <h1>Skill Gaps and Similarity Scores</h1>
      <ul>
        {skillGaps.map((gap, index) => (
          <li key={index}>
            <strong>Skill:</strong> {gap.skill}, <strong>Similarity Score:</strong> {gap.similarity}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Skill;