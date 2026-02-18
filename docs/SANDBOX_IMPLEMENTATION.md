# 🔬 Sandbox Malware Analysis Feature - Implementation Status

**Project:** AI_Aztechs Multi-Agent Cybersecurity System  
**Feature:** Automated Malware Sandbox Analysis with Physical Isolation  
**Implementation Date:** February 17, 2026

---

## ✅ Phase 1 Complete - Foundation (Machine 1)

### What's Been Implemented

#### 1. **Backend Services** ✅
- **Malware Submission Handler** (`backend/services/malware_submission_handler.py`)
  - Accepts user-uploaded malware samples
  - Calculates SHA256 hashes safely (no execution)
  - Stores files in read-only quarantine
  - Validates file size and format
  - Checks for duplicate submissions
  - Sends analysis requests to DMZ (when configured)

- **Analysis Result Processor** (`backend/services/analysis_result_processor.py`)
  - Processes sanitized results from sandbox
  - Integrates with existing BERT classifier
  - Calculates risk scores (0-100)
  - Extracts IOCs (Indicators of Compromise)
  - Generates security recommendations
  - Learns new threat patterns automatically

#### 2. **API Endpoints** ✅
New REST API endpoints in `backend/main.py`:
- `POST /api/sandbox/submit` - Submit malware sample
- `GET /api/sandbox/status/{task_id}` - Check analysis status
- `GET /api/sandbox/results/{task_id}` - Get complete results
- `GET /api/sandbox/list` - List recent submissions
- `POST /api/sandbox/process_result` - Receive results from DMZ
- `GET /api/sandbox/stats` - Sandbox statistics

#### 3. **Database Schema** ✅
Extended `backend/database.py` with new tables:
- `malware_submissions` - Track uploaded samples
- `malware_analysis` - Store analysis results
- `learned_patterns` - New threat patterns for retraining
- Indexes for performance optimization

#### 4. **Frontend Interface** ✅
Professional web-based sandbox viewer (`frontend/sandbox-viewer/`):
- **Upload Tab:** Drag-and-drop malware submission
- **Submissions Tab:** View all submitted samples
- **Results Tab:** Detailed analysis reports with:
  - Threat classification and confidence
  - Risk score with severity levels
  - IOCs (IPs, files, registry keys)
  - Security recommendations
  - Behavioral analysis summary
  - ML model predictions
- **Statistics Tab:** Charts and metrics
- Real-time status tracking
- Modal dialogs for detailed views

#### 5. **Directory Structure** ✅
```
├── backend/services/          # New business logic services
├── quarantine/                # Safe malware storage
│   ├── pending/              # Awaiting analysis
│   ├── analyzed/             # Completed
│   └── rejected/             # Invalid files
├── frontend/sandbox-viewer/   # Web interface
└── docs/                      # Documentation
```

---

## 🚀 How to Use (Current Implementation)

### Starting the System

1. **Activate environment:**
```bash
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system
source venv/bin/activate
```

2. **Start backend API:**
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

3. **Access sandbox interface:**
```bash
# In a new terminal
cd frontend/sandbox-viewer
python -m http.server 8080
```

4. **Open in browser:**
- Sandbox Interface: http://localhost:8080/sandbox.html
- API Documentation: http://localhost:8000/docs

### Submitting Malware Samples

**Via Web Interface:**
1. Go to http://localhost:8080/sandbox.html
2. Click "Upload" tab
3. Drag & drop a file or click "Browse Files"
4. Get task ID for tracking

**Via API:**
```bash
curl -X POST http://localhost:8000/api/sandbox/submit \
  -F "file=@malware_sample.exe" \
  -F "user_id=demo_user"
```

**Response:**
```json
{
  "status": "queued",
  "task_id": "a1b2c3d4...",
  "estimated_time": "5-10 minutes",
  "dmz_status": "dmz_not_configured"
}
```

### Checking Status

```bash
curl http://localhost:8000/api/sandbox/status/a1b2c3d4...
```

### Viewing Results

```bash
curl http://localhost:8000/api/sandbox/results/a1b2c3d4...
```

---

## ⚠️ Current Limitations (Machine 1 Only)

Since we've only implemented the Machine 1 (main application) components:

1. **No Actual Malware Execution**
   - Files are stored but not analyzed yet
   - Need Machine 3 (isolated analysis server) for execution

2. **No DMZ Orchestrator**
   - Need Machine 2 (DMZ bridge) to be configured
   - Currently shows `dmz_not_configured` status

3. **Manual Result Processing**
   - For now, you can manually test the result processor

---

## 🧪 Testing the Implementation

### Test 1: File Upload
```bash
# Create a test file
echo "This is a test malware sample" > test_malware.txt

# Upload via API
curl -X POST http://localhost:8000/api/sandbox/submit \
  -F "file=@test_malware.txt"
```

Expected: Returns task_id and queued status

### Test 2: Check Submissions
```bash
curl http://localhost:8000/api/sandbox/list
```

Expected: Returns list of submissions

### Test 3: Simulate Analysis Result

Create a test script `test_sandbox_result.py`:

```python
import requests
import json

# Simulated analysis result (as it would come from DMZ)
fake_result = {
    'file_hash': 'a1b2c3d4e5f6...', # Replace with actual hash from submission
    'timestamp': '2026-02-17T10:00:00',
    'static_analysis': {
        'file_type': 'PE32 executable',
        'size': 12345,
        'entropy': 7.2
    },
    'behavioral_analysis': {
        'network_connections': [
            {'ip': '192.168.1.100', 'port': 80, 'country': 'US'}
        ],
        'files_created': [
            {'path': 'C:\\\\temp\\\\malware.dll', 'operation': 'create'}
        ],
        'registry_modifications': [
            {'key': 'HKLM\\\\Software\\\\Malware', 'operation': 'create'}
        ],
        'api_calls_summary': {'CreateProcess': 5, 'WriteFile': 10}
    },
    'ml_predictions': {
        'ember_score': 0.95,
        'malconv_score': 0.92,
        'attack_techniques': ['T1055', 'T1059'],
        'c2_confidence': 0.85
    },
    'bert_features': {}
}

# Send to processing endpoint
response = requests.post(
    'http://localhost:8000/api/sandbox/process_result',
    json=fake_result
)

print(response.json())
```

Run: `python test_sandbox_result.py`

Expected: Creates analysis record with BERT classification

### Test 4: View Statistics
```bash
curl http://localhost:8000/api/sandbox/stats
```

Expected: Returns counts and breakdowns

---

## 📋 Next Steps - Phase 2 (Requires Hardware)

### Machine 2: DMZ Orchestrator Setup
- [ ] Purchase Raspberry Pi 4 (8GB) - ~$120
- [ ] Install orchestration layer code
- [ ] Configure dual network interfaces
- [ ] Setup firewall rules
- [ ] Test file transfer to Machine 3

### Machine 3: Analysis Server Setup
- [ ] Acquire/build analysis server - ~$300-400
- [ ] Install Ubuntu Server 22.04
- [ ] Setup KVM virtualization
- [ ] Install CAPE Sandbox
- [ ] Create Windows 10 VM snapshot
- [ ] Configure network isolation
- [ ] Test malware execution in sandbox

### Integration
- [ ] Connect all three machines
- [ ] Verify network isolation
- [ ] Test end-to-end analysis flow
- [ ] Security audit

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```bash
# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# DMZ Configuration (when available)
DMZ_API_URL=http://192.168.1.20:5000
DMZ_API_KEY=your-secret-key

# Quarantine Settings
QUARANTINE_DIR=quarantine
MAX_FILE_SIZE_MB=100

# Database
DB_PATH=backend/incidents.db
```

### Quarantine Directory Permissions

The quarantine directory is automatically created with proper subdirectories. Files are stored with read-only permissions (0o444) to prevent accidental execution.

---

## 🔒 Security Features Implemented

1. ✅ **No Execution on Main Machine**
   - Files are never executed
   - Only hash calculation and metadata extraction

2. ✅ **Read-Only Quarantine**
   - Files stored with 0o444 permissions
   - Prevents accidental execution

3. ✅ **File Validation**
   - Size limits (100MB max)
   - Minimum size check (1KB)
   - Format validation

4. ✅ **Duplicate Detection**
   - SHA256 hash-based deduplication
   - Avoids re-analyzing same files

5. ✅ **Sanitized Results**
   - Result processor only accepts JSON data
   - No binary content allowed
   - All IOCs are text-based

---

## 📊 Database Schema

### malware_submissions
```sql
CREATE TABLE malware_submissions (
    id INTEGER PRIMARY KEY,
    file_hash TEXT UNIQUE,
    original_filename TEXT,
    file_size INTEGER,
    user_id TEXT,
    upload_timestamp TEXT,
    status TEXT,  -- queued/processing/completed/failed
    completed_timestamp TEXT,
    quarantine_path TEXT
);
```

### malware_analysis
```sql
CREATE TABLE malware_analysis (
    id INTEGER PRIMARY KEY,
    file_hash TEXT,
    analysis_timestamp TEXT,
    threat_category TEXT,
    confidence REAL,
    risk_score INTEGER,
    severity TEXT,
    malware_family TEXT,
    attack_techniques TEXT,  -- JSON array
    iocs TEXT,               -- JSON object
    recommendations TEXT,    -- JSON array
    behavioral_summary TEXT,
    full_result TEXT         -- Complete JSON result
);
```

### learned_patterns
```sql
CREATE TABLE learned_patterns (
    id INTEGER PRIMARY KEY,
    file_hash TEXT,
    threat_category TEXT,
    confidence REAL,
    risk_score INTEGER,
    pattern_signature TEXT,  -- JSON
    discovered_timestamp TEXT,
    used_in_training BOOLEAN
);
```

---

## 🎯 Success Metrics

### Current Status
- ✅ Backend services: **100% complete**
- ✅ API endpoints: **100% complete**
- ✅ Frontend interface: **100% complete**
- ✅ Database schema: **100% complete**
- ⏳ DMZ orchestrator: **0% (waiting for hardware)**
- ⏳ Analysis server: **0% (waiting for hardware)**
- ⏳ End-to-end analysis: **0% (dependencies)**

### Overall Phase 1 Progress: **50%**
(Machine 1 complete, Machines 2&3 pending hardware)

---

## 🐛 Troubleshooting

### Issue: "DMZ not configured" status
**Solution:** This is expected. DMZ orchestrator (Machine 2) is not yet setup. For now, you can:
- Test file uploads
- View submissions list
- Manually test result processing with simulated data

### Issue: Database errors
**Solution:** Ensure database file exists and has write permissions:
```bash
ls -la backend/incidents.db
chmod 644 backend/incidents.db
```

### Issue: File upload fails
**Solution:** Check:
- File size < 100MB
- File size > 1KB
- Quarantine directory exists and is writable

### Issue: BERT model not found
**Solution:** Train the model first:
```bash
python train_bert_model.py
```

---

## 📚 API Documentation

Full interactive API documentation available at:
http://localhost:8000/docs

Key endpoints:
- Sandbox operations: `/api/sandbox/*`
- Log analysis: `/analyze`
- Incidents: `/incidents`
- Statistics: `/stats`

---

## 💻 Development

### Project Structure
```
backend/
├── main.py              # FastAPI app with sandbox endpoints
├── database.py          # Extended with malware tables
├── models.py            # Pydantic models
└── services/            # NEW
    ├── malware_submission_handler.py
    └── analysis_result_processor.py

frontend/
├── index.html           # Main dashboard
├── app.js
├── style.css
└── sandbox-viewer/      # NEW
    ├── sandbox.html
    ├── sandbox.js
    └── sandbox.css

quarantine/              # NEW
├── pending/
├── analyzed/
└── rejected/
```

### Adding Custom Features

**Example: Add new IOC type**

1. Update `analysis_result_processor.py`:
```python
def _extract_iocs(self, result: Dict) -> Dict[str, List]:
    iocs = {
        'ip_addresses': [],
        'domains': [],
        'file_paths': [],
        'registry_keys': [],
        'mutexes': [],
        'urls': []  # NEW
    }
    # ... extraction logic
```

2. Update frontend display in `sandbox.js`:
```javascript
if (iocs.urls && iocs.urls.length > 0) {
    html += '<h4>URL IOCs:</h4><ul>';
    // ... rendering logic
}
```

---

## 🎉 What's Working Right Now

You can currently:
1. ✅ Upload malware samples via web or API
2. ✅ View all submissions in a table
3. ✅ Track submission status
4. ✅ See sandbox statistics
5. ✅ Test result processing with simulated data
6. ✅ View professional analysis reports
7. ✅ Extract IOCs from analysis results
8. ✅ Get security recommendations
9. ✅ Integrate with existing BERT classifier
10. ✅ Learn new threat patterns

---

## 📞 Support

For issues or questions:
1. Check API logs: Look at terminal running `uvicorn`
2. Check browser console: Press F12 in browser
3. Review database: `sqlite3 backend/incidents.db`
4. Check quarantine: `ls -la quarantine/pending/`

---

**Implementation Status:** Phase 1 (Machine 1) Complete! ✅  
**Next Milestone:** Acquire hardware for Machines 2 & 3

---

*Last Updated: February 17, 2026*
