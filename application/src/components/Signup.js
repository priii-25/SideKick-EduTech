import React, { useState } from 'react';
import Select from 'react-select';
import { TextField, Button, Container, Grid, Typography, Box } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';

const skillsOptions = [
  { value: 'JavaScript', label: 'JavaScript' },
  { value: 'React', label: 'React' },
  { value: 'Node.js', label: 'Node.js' },
  { value: 'Python', label: 'Python' },
  { value: 'Java', label: 'Java' },
  { value: 'C++', label: 'C++' },
  { value: 'Ruby', label: 'Ruby' },
  { value: 'PHP', label: 'PHP' },
  { value: 'Swift', label: 'Swift' },
  { value: 'Kotlin', label: 'Kotlin' },
];

const positionsOptions = [
  { value: 'Software Engineer', label: 'Software Engineer' },
  { value: 'Frontend Developer', label: 'Frontend Developer' },
  { value: 'Backend Developer', label: 'Backend Developer' },
  { value: 'Full Stack Developer', label: 'Full Stack Developer' },
  { value: 'Data Scientist', label: 'Data Scientist' },
  { value: 'DevOps Engineer', label: 'DevOps Engineer' },
  { value: 'Product Manager', label: 'Product Manager' },
  { value: 'Project Manager', label: 'Project Manager' },
  { value: 'UI/UX Designer', label: 'UI/UX Designer' },
  { value: 'Mobile Developer', label: 'Mobile Developer' },
  { value: 'QA Engineer', label: 'QA Engineer' },
  { value: 'Business Analyst', label: 'Business Analyst' },
  { value: 'System Administrator', label: 'System Administrator' },
  { value: 'Security Engineer', label: 'Security Engineer' },
];

const theme = createTheme({
  typography: {
    h4: {
      color: '#000',
    },
  },
});

const Signup = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    skills: [],
    position: '',
    resume: null,
    academicHistory: '',
    careerAspirations: '',
    preferences: '',
  });
  const handleSubmit = async (e) => {
    e.preventDefault();
  
    const formDataToSend = {
      firstName: formData.firstName,
      lastName: formData.lastName,
      skills: formData.skills.map((skill) => skill.value || skill),
      position: formData.position?.value || '',
      resume: formData.resume || null,
      academicHistory: formData.academicHistory,
      careerAspirations: formData.careerAspirations,
      preferences: formData.preferences,
    };
    
  
    try {
      const response = await fetch('http://localhost:5000/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formDataToSend),
      });
  
      if (response.ok) {
        alert('Profile saved successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to save profile: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error occurred while saving the profile.');
    }
  };
  
  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSkillsChange = (selectedOptions) => {
    setFormData({
      ...formData,
      skills: selectedOptions,
    });
  };

  const handlePositionChange = (selectedOption) => {
    setFormData({
      ...formData,
      position: selectedOption,
    });
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('resume', file);
  
    try {
      const response = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
      });
  
      const data = await response.json();
      setFormData({
        ...formData,
        resume: data.file.filePath, 
      });
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };
    
  
  return (
    <ThemeProvider theme={theme}>
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(to right, rgb(133, 178, 121), rgb(236, 249, 237))',
          padding: '2rem',
        }}
      >
        <Container maxWidth="md">
            <Typography variant="h4" align="center" gutterBottom>
              Sign Up Page
            </Typography>
            <form onSubmit={handleSubmit}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="First Name"
                    name="firstName"
                    variant="outlined"
                    value={formData.firstName}
                    onChange={handleChange}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Last Name"
                    name="lastName"
                    variant="outlined"
                    value={formData.lastName}
                    onChange={handleChange}
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <Select
                    isMulti
                    options={skillsOptions}
                    value={formData.skills}
                    onChange={handleSkillsChange}
                    placeholder="Select your skills"
                    styles={{
                      control: (base) => ({
                        ...base,
                        background: 'rgba(255, 255, 255, 0.1)',
                        borderColor: 'rgba(255, 255, 255, 0.5)',
                      }),
                      menu: (base) => ({
                        ...base,
                        background: 'rgba(255, 255, 255, 0.9)',
                      }),
                      singleValue: (base) => ({
                        ...base,
                      }),
                    }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Select
                    options={positionsOptions}
                    value={formData.position}
                    onChange={handlePositionChange}
                    placeholder="Select the position you're aiming for"
                    styles={{
                      control: (base) => ({
                        ...base,
                        background: 'rgba(255, 255, 255, 0.1)',
                        borderColor: 'rgba(255, 255, 255, 0.5)',
                      }),
                      menu: (base) => ({
                        ...base,
                        background: 'rgba(255, 255, 255, 0.9)',
                      }),
                      singleValue: (base) => ({
                        ...base,
                      }),
                    }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Academic History"
                    name="academicHistory"
                    variant="outlined"
                    multiline
                    rows={4}
                    value={formData.academicHistory}
                    onChange={handleChange}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Career Aspirations"
                    name="careerAspirations"
                    variant="outlined"
                    multiline
                    rows={4}
                    value={formData.careerAspirations}
                    onChange={handleChange}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Personalized Preferences"
                    name="preferences"
                    variant="outlined"
                    multiline
                    rows={4}
                    value={formData.preferences}
                    onChange={handleChange}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    component="label"
                    style={{ backgroundColor: '#000', color: '#ff7e5f' }}
                  >
                    Upload Resume
                    <input
                      type="file"
                      hidden
                      onChange={handleFileChange}
                    />
                  </Button>
                </Grid>
                <Grid item xs={12}>
                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    style={{ backgroundColor: '#000', color: '#ff7e5f' }}
                  >
                    Submit
                  </Button>
                </Grid>
              </Grid>
            </form>
        </Container>
      </Box>
    </ThemeProvider>
  );
};

export default Signup;