# 🏠 Agentic Home Threat Detection System

An intelligent, multi-agent system for real-time home threat detection using Google ADK and AI Studio.

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Running the System](#running-the-system)
6. [Demo Script](#demo-script)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

This system implements a multi-agent architecture for home security:

- **5 Camera Agents**: Process video feeds from different locations
- **Sensor Agent**: Monitors smartwatch, accelerometer, microphone, and smoke detectors
- **Orchestrator Agent**: Makes intelligent escalation decisions based on threat analysis
- **Vision Detector**: Uses Google Gemini for image-based threat detection
- **Vector Store**: Stores temporal event data in Pinecone for historical analysis

### Architecture Components
```
Video Feeds → Kafka → Camera Agents → Vision AI → Threat Analysis
Sensors → Kafka → Sensor Agent → Analysis → Orchestrator → Alerts
                                               ↓
                                        Vector Store (Pinecone)
                                               ↓
                                        WebSocket → Frontend
```

---

## ✅ Prerequisites

### Software Requirements
- **Windows 10/11** with Docker Desktop installed
- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/))

### API Keys Required
1. **Google AI Studio API Key**
   - Visit: https://aistudio.google.com/
   - Sign in with Google account
   - Click "Get API Key" → "Create API Key"
   - Copy the key

2. **Pinecone API Key**
   - Visit: https://www.pinecone.io/
   - Sign up for free account
   - Go to API Keys section
   - Copy your API key and environment

---

## 🚀 Installation Steps

### Step 1: Clone and Setup Directory Structure

```powershell
# Clone your repository
cd path\to\your\repository

# Verify structure exists (created from artifact)
# If not, create directories as shown in the project structure artifact
```

### Step 2: Setup Python Backend

```powershell
# Navigate to project root
cd threat-detection-system

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install Python dependencies
pip install -r backend/requirements.txt
```

### Step 3: Setup Frontend

```powershell
# Open a NEW PowerShell window
cd threat-detection-system\frontend

# Install Node dependencies
npm install
```

### Step 4: Setup Docker (Kafka)

```powershell
# Ensure Docker Desktop is running

# Start Kafka and Zookeeper
docker-compose up -d

# Verify containers are running
docker ps

# You should see:
# - zookeeper
# - kafka
# - kafka-ui

# Access Kafka UI at: http://localhost:8080
```

### Step 5: Configure Environment Variables

```powershell
# Copy example env file
cp backend\.env.example backend\.env

# Edit backend/.env with your API keys
notepad backend\.env
```

Update these values:
```env
GOOGLE_API_KEY=your_actual_google_api_key
PINECONE_API_KEY=your_actual_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_region  # e.g., us-east-1
```

### Step 6: Prepare Sample Videos

For the demo, you'll need 5 sample videos. Place them in `sample_videos/` directory:

- `camera1_normal.mp4` - Normal household activity
- `camera2_weapon.mp4` - Simulated weapon detection scenario
- `camera3_fall.mp4` - Person falling or on ground
- `camera4_fire.mp4` - Smoke or fire scenario
- `camera5_crowd.mp4` - Multiple people scenario

**Option 1**: Use your own videos (recommended for demo)
**Option 2**: Use placeholder videos (system will log warnings but continue)
**Option 3**: Use stock footage from sites like Pexels or Pixabay

### Step 7: Initialize Pinecone Index

The system will auto-create the Pinecone index on first run, but you can verify:

```python
# Optional: Test Pinecone connection
python -c "from backend.storage.vector_store import get_vector_store; get_vector_store()"
```

---

## ⚙️ Configuration

### Backend Settings
Edit `backend/config/settings.py` to customize:

- **Frame interval**: How often to extract frames (default: 5 seconds)
- **Simulation speed**: Speed up playback for demo (1.0 = real-time, 2.0 = 2x)
- **Threat thresholds**: Confidence levels for detection
- **Alert timeouts**: Response time windows

### Frontend Configuration
The frontend auto-connects to `localhost:8000`. If you change the API port, update `frontend/src/App.jsx`.

---

## 🎬 Running the System

### Quick Start (All Components)

**Terminal 1 - Backend + Agents:**
```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Run the backend
python backend/main.py
```

You should see:
```
🏠 AGENTIC HOME THREAT DETECTION SYSTEM
Initializing Orchestrator Agent...
Initializing Camera Agents...
Starting 5 camera agents...
✅ SYSTEM FULLY OPERATIONAL
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

Access the dashboard at: **http://localhost:3000**

### Verify System is Running

1. **Kafka UI**: http://localhost:8080
   - Check topics: camera-1 through camera-5, sensors, alerts

2. **API Health Check**: http://localhost:8000
   - Should return: `{"status": "running"}`

3. **Frontend Dashboard**: http://localhost:3000
   - Should show device statuses and real-time alerts

---

## 🎭 Demo Script

### Pre-Demo Checklist
- [ ] Docker containers running
- [ ] Backend running and showing "SYSTEM FULLY OPERATIONAL"
- [ ] Frontend loaded at localhost:3000
- [ ] Sample videos in place
- [ ] API keys configured correctly
- [ ] Test alerts appearing on dashboard

### Demo Flow (15-20 minutes)

#### 1. Introduction (2 min)
"This is an agentic AI system that uses Google's AI capabilities to detect threats in a home environment using multiple sensors and cameras."

**Show**: Dashboard with all devices online

#### 2. System Architecture (3 min)
Explain the multi-agent architecture:
- "We have 5 camera agents processing video feeds independently"
- "Each agent uses Google's Gemini vision model for threat detection"
- "A central orchestrator makes intelligent escalation decisions"
- "All events are stored in Pinecone for historical analysis"

**Show**: Terminal logs showing agents starting up

#### 3. Normal Operations (2 min)
"Under normal conditions, the system monitors continuously but generates no alerts."

**Show**: Dashboard showing Camera 1 (normal) with no alerts

#### 4. Threat Detection Scenarios (8 min)

**Scenario A: Weapon Detection (Critical)**
- Camera 2 detects weapon with unfamiliar person
- **Expected**: CRITICAL alert, recommendation to call 911
- **Show**: Alert appears in dashboard, incident modal with details

**Scenario B: Fall Detection (High)**
- Camera 3 shows person on ground
- Accelerometer detects fall
- **Expected**: HIGH alert, vitals check initiated
- **Show**: Correlated alerts from multiple sensors

**Scenario C: Fire Detection (Critical)**
- Camera 4 detects smoke/fire
- Smoke detector triggers
- **Expected**: CRITICAL alert, emergency services notification
- **Show**: Multiple alert types converging

**Scenario D: Audio Threat (Medium)**
- Microphone detects scream
- **Expected**: MEDIUM alert, camera review requested
- **Show**: Audio-triggered camera correlation

#### 5. Orchestrator Decision Making (3 min)
"The orchestrator implements sophisticated decision logic from the specification."

Walk through the decision tree:
1. Weapon + Unfamiliar → Call 911
2. Vitals check → Text → Call → Emergency contact
3. Camera disconnect → Recovery attempts
4. Fire detection → Immediate emergency response

**Show**: Terminal logs showing orchestrator reasoning

#### 6. Historical Analysis (2 min)
"All events are stored in Pinecone for pattern analysis and incident review."

**Show**: History view with past incidents

#### 7. Q&A Highlights
Be prepared to answer:
- "How does it handle false positives?" → Confidence thresholds, human-in-the-loop
- "What about privacy?" → Mentioned CCPA/HIPAA considerations
- "Can it scale?" → Yes, distributed architecture with Kafka
- "Response time?" → Real-time processing, sub-second alerts

### Demo Tips
1. **Rehearse transitions** between scenarios
2. **Have backup plans** if videos don't cooperate
3. **Show terminal logs** - they're impressive
4. **Emphasize the AI** - Google's Gemini doing the vision work
5. **Highlight agentic behavior** - agents making autonomous decisions
6. **Keep energy high** - this is exciting technology!

---

## 🐛 Troubleshooting

### Kafka Won't Start
```powershell
# Check if ports are in use
netstat -ano | findstr "9092"

# Stop and restart containers
docker-compose down
docker-compose up -d
```

### Python Import Errors
```powershell
# Ensure you're in venv
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r backend/requirements.txt --force-reinstall
```

### Frontend Won't Connect to Backend
1. Check backend is running: http://localhost:8000
2. Check CORS settings in `backend/api/server.py`
3. Verify WebSocket connection in browser console

### Google API Errors
- Verify API key is correct
- Check you've enabled the Generative AI API in Google Cloud Console
- Ensure you have quota remaining

### Pinecone Connection Issues
- Verify API key and environment
- Check index name matches in settings
- Ensure you have free tier quota

### Video Processing Issues
- Check video codec (H.264 recommended)
- Verify OpenCV can read the files
- Try re-encoding videos with HandBrake

### No Alerts Appearing
1. Check Kafka topics have messages: http://localhost:8080
2. Verify agents are consuming (check logs)
3. Ensure threshold settings aren't too strict

---

## 📊 System Monitoring

### Useful Commands

**Check System Status:**
```powershell
# API health
curl http://localhost:8000

# Active alerts
curl http://localhost:8000/api/alerts

# Device status
curl http://localhost:8000/api/devices
```

**Monitor Logs:**
```powershell
# Backend logs are in logs/ directory
Get-Content logs\threat_detection_*.log -Tail 50 -Wait
```

**Kafka Monitoring:**
- UI: http://localhost:8080
- Topics: camera-1 to camera-5, sensors, alerts

---

## 🎯 Next Steps

### Enhancements for Production
1. **Authentication**: Add OAuth for frontend
2. **Encryption**: TLS for all communications
3. **Compliance**: Full CCPA/HIPAA implementation
4. **Cloud Deployment**: AWS/GCP infrastructure
5. **Real Hardware**: Integrate with actual cameras and sensors
6. **ML Training**: Fine-tune detection models
7. **Mobile App**: iOS/Android companion apps
8. **Alert Routing**: SMS, email, push notifications

### Performance Optimization
1. **Batch Processing**: Group frames for efficiency
2. **Edge Computing**: Process on local devices
3. **Caching**: Redis for frequently accessed data
4. **Load Balancing**: Multiple agent instances

---

## 📝 Demo Presentation Slides Outline

1. **Title Slide**: Agentic Home Threat Detection
2. **Problem Statement**: Home security challenges
3. **Solution Overview**: Multi-agent AI system
4. **Architecture Diagram**: Show component interaction
5. **Technology Stack**: Google ADK, Gemini, Pinecone, Kafka
6. **Live Demo**: (your actual demo)
7. **Results**: Detection accuracy, response times
8. **Compliance**: CCPA/HIPAA considerations
9. **Future Roadmap**: Production enhancements
10. **Q&A**

---

## 📞 Support

For issues during setup or demo:
1. Check logs in `logs/` directory
2. Verify all services running: `docker ps`, API health check
3. Review this troubleshooting section
4. Check console output for specific error messages

---

## 🎉 Success Criteria

Your demo is successful if:
- ✅ All 9 devices show "online"
- ✅ Alerts appear in real-time on dashboard
- ✅ Multiple threat scenarios trigger correctly
- ✅ Orchestrator makes appropriate escalation decisions
- ✅ Historical events stored and retrievable
- ✅ System handles continuous operation for demo duration
