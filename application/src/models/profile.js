const mongoose = require('mongoose');

const ProfileSchema = new mongoose.Schema({
  firstName: { type: String, required: true },
  lastName: { type: String, required: true },
  skills: { type: [String], required: true },
  position: { type: String },
  resume: { type: Buffer },
  resumeMimeType: { type: String },//retrieval purposess
  academicHistory: { type: String, required: false },
  careerAspirations: { type: String, required: false },
  preferences: { type: String, required: false },
}, { timestamps: true });

module.exports = mongoose.model('Profile', ProfileSchema);
