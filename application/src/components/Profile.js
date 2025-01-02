import React, { useEffect, useState } from 'react';

const Profile = () => {
  const profileId = "67770940251837714047c780"; 

  const [profile, setProfile] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      const response = await fetch(`http://localhost:5000/api/profile/${profileId}`);
      const data = await response.json();
      setProfile(data);
    };

    fetchProfile();
  }, [profileId]);

  if (!profile) {
    return <p>Loading...</p>;
  }

  return (
    <div className="profile">
      <h2>My Profile</h2>
      <p>Name: {profile.firstName} {profile.lastName}</p>
      <p>Position: {profile.position}</p>
      <p>Academic History: {profile.academicHistory}</p>
      <p>Career Aspirations: {profile.careerAspirations}</p>
      <p>Preferences: {profile.preferences}</p>
      <a href={`http://localhost:5000/api/profile/${profileId}/resume`} download className="btn">Download Resume</a>
    </div>
  );
};

export default Profile;
