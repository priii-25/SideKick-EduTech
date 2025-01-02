require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bodyParser = require('body-parser');
const Profile = require('./models/profile');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static('uploads'));

// MongoDB Connection
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
  .then(() => console.log('MongoDB connected'))
  .catch((err) => console.error(err));

// API Route
app.post('/api/profile', async (req, res) => {
  try {
    const { firstName, lastName, skills, position, academicHistory, careerAspirations, preferences, resume } = req.body;

    const newProfile = new Profile({
        firstName,
        lastName,
        skills: skills && skills.length > 0 ? skills : [],
        position: position || '', 
        academicHistory,
        careerAspirations,
        preferences,
        resume,
      });
      

    await newProfile.save();
    res.status(201).json({ message: 'Profile saved successfully!' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Server error' });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
 
const multer = require('multer');
const path = require('path');
const File = require('./models/file');

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, path.join(__dirname, 'uploads'));
  },
  filename: (req, file, cb) => {
    cb(null, `${Date.now()}-${file.originalname}`);
  },
});

const upload = multer({ storage });

app.post('/api/upload', upload.single('resume'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const newFile = new File({
      originalName: req.file.originalname,
      filePath: `/uploads/${req.file.filename}`,
      mimeType: req.file.mimetype,
      size: req.file.size,
    });

    const savedFile = await newFile.save();

    res.status(201).json({
      message: 'File uploaded and saved successfully',
      file: savedFile,
    });
  } catch (error) {
    console.error('Error uploading file:', error);
    res.status(500).json({ error: 'Server error' });
  }
});
