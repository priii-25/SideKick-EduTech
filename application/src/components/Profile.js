import React from 'react';

const Profile = () => {
  return (
    <div className="profile">
      <h2>My Profile</h2>
      <p>Name: [Candidate Name]</p>
      <p>Email: [Candidate Email]</p>
      <a href="/resume.pdf" download className="btn">Download Resume</a>
    </div>
  );
};

export default Profile;
