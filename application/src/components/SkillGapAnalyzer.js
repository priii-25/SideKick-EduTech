import React, { useState, useEffect } from 'react';

const SkillGapAnalyzer = () => {
  const [userSkills, setUserSkills] = useState([]);
  const [currentSkill, setCurrentSkill] = useState('');
  const [careerPaths, setCareerPaths] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    initializeSystem();
  }, []);

  const initializeSystem = async () => {
    try {
      const response = await fetch('http://localhost:8000/initialize');
      const data = await response.json();
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize system:', error);
    }
  };

 
  const handleAddSkill = () => {
    const trimmedSkill = currentSkill.trim();
    if (trimmedSkill && !userSkills.includes(trimmedSkill)) {
      setUserSkills([...userSkills, trimmedSkill]);
      setCurrentSkill('');
    }
  };
  const handleRemoveSkill = (skillToRemove) => {
    setUserSkills(userSkills.filter(skill => skill !== skillToRemove));
  };
  const handleAnalyze = async () => {
    if (userSkills.length === 0) return;

    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/analyze-skills', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ skills: userSkills }),
      });
      const data = await response.json();
      
      if (data.career_paths) {
        setCareerPaths(data.career_paths);
      } else if (data.error) {
        console.error('Error from backend:', data.error);
      } else {
        console.error('Unexpected response format:', data);
      }
    } catch (error) {
      console.error('Failed to analyze skills:', error);
    }
    setIsLoading(false);
  };

  
  const getColor = (score) => {
    const hue = (score * 120).toString(10);
    return `hsl(${hue}, 70%, 50%)`;
  };

  return (
    <div style={{
      maxWidth: '800px',
      margin: '2rem auto',
      padding: '1.5rem',
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f9fafb'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        padding: '1.5rem'
      }}>
        <h2 style={{
          fontSize: '1.5rem',
          fontWeight: 'bold',
          marginBottom: '1.5rem'
        }}>Skill Gap Analyzer</h2>

        <div style={{
          display: 'flex',
          gap: '0.5rem',
          marginBottom: '1rem'
        }}>
          <input
            type="text"
            value={currentSkill}
            onChange={(e) => setCurrentSkill(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddSkill()}
            placeholder="Enter a skill..."
            style={{
              flex: 1,
              padding: '0.5rem',
              borderRadius: '4px',
              border: '1px solid #ccc'
            }}
          />
          <button
            onClick={handleAddSkill}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Add Skill
          </button>
        </div>

        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginBottom: '1rem'
        }}>
          {userSkills.map((skill, index) => (
            <div
              key={index}
              style={{
                backgroundColor: '#dbeafe',
                color: '#1e40af',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              {skill}
              <button
                onClick={() => handleRemoveSkill(skill)}
                style={{
                  border: 'none',
                  background: 'none',
                  color: '#1e40af',
                  cursor: 'pointer',
                  padding: '2px'
                }}
              >
                ×
              </button>
            </div>
          ))}
        </div>

        <button
          onClick={handleAnalyze}
          disabled={!isInitialized || userSkills.length === 0 || isLoading}
          style={{
            width: '100%',
            padding: '0.75rem',
            backgroundColor: isInitialized && userSkills.length > 0 && !isLoading ? '#2563eb' : '#9ca3af',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isInitialized && userSkills.length > 0 && !isLoading ? 'pointer' : 'not-allowed',
            marginBottom: '1rem'
          }}
        >
          {isLoading ? 'Analyzing...' : 'Analyze Skills'}
        </button>

        {careerPaths.length > 0 && (
          <div>
            <h3 style={{
              fontSize: '1.125rem',
              fontWeight: 'bold',
              marginBottom: '1rem'
            }}>Career Path Recommendations:</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {careerPaths.map((path, index) => (
                <div
                  key={index}
                  style={{
                    padding: '0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    backgroundColor: '#f3f4f6'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: '500' }}>{path.profession}</span>
                    <span style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '9999px',
                      fontSize: '0.875rem',
                      backgroundColor: '#2563eb',
                      color: 'white'
                    }}>
                      {path.match_score}% match
                    </span>
                  </div>
                  <div style={{ marginTop: '0.5rem' }}>
                    <strong>Matching Skills:</strong> {path.matching_skills.join(', ') || 'None'}
                  </div>
                  <div style={{ marginTop: '0.5rem' }}>
                    <strong>Missing Skills:</strong> {path.missing_skills.join(', ') || 'None'}
                  </div>
                  {path.missing_skills_by_domain && Object.keys(path.missing_skills_by_domain).length > 0 && (
                    <div style={{ marginTop: '0.5rem' }}>
                      <strong>Missing Skills by Domain:</strong>
                      <ul>
                        {Object.entries(path.missing_skills_by_domain).map(([domain, skills], idx) => (
                          <li key={idx}>
                            <strong>{domain}:</strong> {skills.join(', ')}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {path.related_professions && path.related_professions.length > 0 && (
                    <div style={{ marginTop: '0.5rem' }}>
                      <strong>Related Professions:</strong> {path.related_professions.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SkillGapAnalyzer;