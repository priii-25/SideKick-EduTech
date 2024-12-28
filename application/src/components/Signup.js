import React, { useState } from 'react';

const Signup = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    resume: null,
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleFileChange = (e) => {
    setFormData({ ...formData, resume: e.target.files[0] });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Form submitted:', formData);
  };

  return (
    <div className="signup">
      <h2>Sign Up</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Name:
          <input type="text" name="name" value={formData.name} onChange={handleInputChange} required />
        </label>
        <label>
          Email:
          <input type="email" name="email" value={formData.email} onChange={handleInputChange} required />
        </label>
        <label>
          Upload Resume:
          <input type="file" name="resume" onChange={handleFileChange} required />
        </label>
        <button type="submit">Sign Up</button>
      </form>
    </div>
  );
};

export default Signup;
