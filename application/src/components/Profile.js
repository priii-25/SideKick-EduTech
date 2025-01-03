import React, { useEffect, useState } from 'react';
import './profile.css'; 

const Profile = () => {
  const profileId = "67770940251837714047c780"; 
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/profile/${profileId}`);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
  
        if (typeof data.skills === 'string') {
          try {
            data.skills = JSON.parse(data.skills);
            console.log("Parsed skills:", data.skills);
          } catch (error) {
            console.error("Error parsing skills:", error);
            data.skills = []; 
            console.log("Parsed skills:", data.skills);
          }
        }
  
        setProfile(data);
      } catch (error) {
        console.error("Error fetching profile:", error);
      }
    };
  
    fetchProfile();
  }, [profileId]);
  
  if (!profile) {
    return (
      <div className="profile-container">
        <div className="profile-card">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <div className="profile-card">
        <h2>My Profile</h2>
        <div className="profile-name">
          {profile.firstName} {profile.lastName}
        </div>
        <div className="profile-details">
          <div className="detail-row">
            <span className="detail-label">Position:</span>
            <span className="detail-content">{profile.position}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Academic History:</span>
            <span className="detail-content">{profile.academicHistory}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Career Aspirations:</span>
            <span className="detail-content">{profile.careerAspirations}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Preferences:</span>
            <span className="detail-content">{profile.preferences}</span>
          </div>
        </div>
        <div className="skills-section">
          <strong>Skills:</strong>
          <div className="skills-list">
  {Array.isArray(profile.skills) && profile.skills.length > 0 ? (
    profile.skills.map((skill, index) => (
      <span key={index} className={`skill-badge ${skill.toLowerCase()}-badge`}>
        {skill}
      </span>
    ))
  ) : (
    <span>No skills available</span>
  )}
</div>

        </div>
        <a
          href={`http://localhost:5000/api/profile/${profileId}/resume`}
          download
          className="download-btn"
        >
          Download Resume
        </a>
      </div>
    </div>
  );
};

export default Profile;