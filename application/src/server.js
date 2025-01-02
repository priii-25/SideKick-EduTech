require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bodyParser = require('body-parser');
const multer = require('multer');
const Profile = require('./models/profile');
const storage = multer.memoryStorage();
const upload = multer({ storage });

const app = express();
const PORT = process.env.PORT || 5000;

// Middlewares
app.use(cors());
app.use(bodyParser.json());
app.use(express.static('uploads'));

mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
  .then(() => console.log('MongoDB connected'))
  .catch((err) => console.error(err));

// API Routes
app.post('/api/profile', upload.single('resume'), async (req, res) => {
  try {
    const { firstName, lastName, skills, position, academicHistory, careerAspirations, preferences } = req.body;

    const newProfile = new Profile({
      firstName,
      lastName,
      skills: skills && skills.length > 0 ? skills : [],
      position: position || '',
      academicHistory,
      careerAspirations,
      preferences,
    });

    if (req.file) {
      newProfile.resume = req.file.buffer;
      newProfile.resumeMimeType = req.file.mimetype;
    }

    await newProfile.save();

    res.status(201).json({ message: 'Profile with resume saved successfully!', profileId: newProfile._id });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
});

app.get('/api/profile/:id', async (req, res) => {
  try {
    const profile = await Profile.findById(req.params.id);

    if (!profile) {
      return res.status(404).json({ error: 'Profile not found' });
    }

    res.json(profile);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
});

app.get('/api/profile/:id/resume', async (req, res) => {
  try {
    const profile = await Profile.findById(req.params.id);

    if (!profile || !profile.resume) {
      return res.status(404).json({ error: 'Resume not found' });
    }

    res.set('Content-Type', profile.resumeMimeType);
    res.send(profile.resume);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
