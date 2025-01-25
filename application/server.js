require('dotenv').config();
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const multer = require('multer');
const mongoose = require('mongoose');
const neo4j = require('neo4j-driver');
const Profile = require('./src/models/profile');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(bodyParser.json());
app.use(express.static('uploads'));
app.use(express.json());

const storage = multer.memoryStorage();
const upload = multer({ storage });

mongoose.connect('mongodb://localhost:27017/', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
  .then(() => console.log('MongoDB connected'))
  .catch((err) => console.error(err));

  const driver = neo4j.driver(
    'bolt://localhost:7687',
    neo4j.auth.basic('neo4j', 'priyanshi'),
    { encrypted: 'ENCRYPTION_OFF' }
  );

  app.get('/api/graph-data', async (req, res) => {
  const session = driver.session({ database: 'jobsskills' });
  try {
    const result = await session.run(`
      MATCH (n)-[r]->(m)
      RETURN
        id(n) AS sourceId,
        n.name AS sourceName,
        id(m) AS targetId,
        m.name AS targetName,
        type(r) AS relationshipType
    `);

    const nodesMap = {};
    const edges = [];

    result.records.forEach(record => {
      const sourceId = record.get('sourceId').toString();
      const sourceName = record.get('sourceName');
      const targetId = record.get('targetId').toString();
      const targetName = record.get('targetName');
      const relationshipType = record.get('relationshipType');

      if (!nodesMap[sourceId]) {
        nodesMap[sourceId] = { id: sourceId, label: sourceName };
      }
      if (!nodesMap[targetId]) {
        nodesMap[targetId] = { id: targetId, label: targetName };
      }

      edges.push({
        from: sourceId,
        to: targetId,
        label: relationshipType
      });
    });

    const nodes = Object.values(nodesMap);
    res.json({ nodes, edges });
  } catch (error) {
    console.error('Error fetching graph data from Neo4j:', error);
    res.status(500).send('Error fetching graph data from Neo4j');
  } finally {
    await session.close();
  }
});

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