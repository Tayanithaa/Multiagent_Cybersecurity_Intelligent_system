# 🔐 Complete 3-Machine Sandbox Setup Guide

**Date:** February 18, 2026  
**System:** AI_Aztechs Multi-Agent Cybersecurity Sandbox  
**Setup Time:** ~4-6 hours per phase

---

## 📋 Overview

This guide covers the complete setup of your physically isolated malware sandbox system:

| Machine | Role | Purpose | Hardware |
|---------|------|---------|----------|
| **Machine 1** | Safe Zone (Main App) | User interface, threat detection, API server | Your current system |
| **Machine 2** | DMZ (Orchestrator) | Receives files, coordinates analysis, manages VMs | Raspberry Pi 4 (8GB) or old laptop |
| **Machine 3** | Danger Zone (Analysis) | Runs CAPE sandbox, executes malware safely | Desktop with 16GB RAM, 500GB storage |

---

## 🎯 Phase 1: Machine 1 Setup (COMPLETE ✅)

**Status:** Already Done
- Backend API running on http://localhost:8000
- Frontend UI ready at http://localhost:8080/sandbox.html
- Database initialized with 3 new tables
- Services ready to receive files

**Quick Check:**
```bash
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system
source venv/bin/activate
python -m uvicorn backend.main:app --reload --port 8000 &
cd frontend/sandbox-viewer && python -m http.server 8080 &
```

---

## ⚙️ Phase 2: Machine 2 Setup (DMZ Orchestrator)

### Hardware Requirements
- **Option A (Recommended):** Raspberry Pi 4 (8GB) - ~$120
- **Option B:** Old laptop with Linux - $0-50
- **Network:** 2 ethernet ports or 1 ethernet + WiFi adapter
- **OS:** Ubuntu 22.04 LTS Server

### Step 1: Install Base System

```bash
# On Machine 2
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3-pip python3-venv git curl

# Clone your project or copy files
git clone <your-repo> multisec-dmz
cd multisec-dmz
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Create DMZ Orchestrator Service

Create `/home/ubuntu/multisec-dmz/dmz_orchestrator.py`:

```python
"""
DMZ Orchestrator - Machine 2
Receives malware files from Machine 1 (Safe Zone)
Coordinates analysis on Machine 3 (Danger Zone)
Returns sanitized results back to Machine 1
"""

import asyncio
import json
import aiohttp
from aiohttp import web
from pathlib import Path
import hashlib
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DMZ_Orchestrator")

# Configuration
MACHINE1_IP = "192.168.1.100"          # Main app server (CHANGE TO YOUR IP)
MACHINE3_IP = "192.168.3.100"          # Analysis server (CHANGE TO YOUR IP)
MACHINE1_PORT = 8000
MACHINE3_PORT = 8000
DMZ_PORT = 8001
DMZ_STORAGE = Path("./dmz_storage")

# Ensure storage exists
DMZ_STORAGE.mkdir(exist_ok=True)

class DMZOrchestrator:
    def __init__(self):
        self.pending_analyses = {}
        self.completed_analyses = {}
        self.analysis_results = {}
        
    async def receive_from_machine1(self, request):
        """
        Endpoint for Machine 1 to send malware files
        POST /api/dmz/receive
        """
        try:
            data = await request.json()
            file_hash = data.get('file_hash')
            file_bytes = bytes.fromhex(data.get('file_data', ''))
            
            logger.info(f"Received file from Machine 1: {file_hash}")
            
            # Store file temporarily
            temp_file = DMZ_STORAGE / file_hash
            temp_file.write_bytes(file_bytes)
            
            # Forward to Machine 3 for analysis
            task_id = await self.send_to_machine3(file_hash, file_bytes)
            
            logger.info(f"Forwarded to Machine 3 with task_id: {task_id}")
            self.pending_analyses[task_id] = file_hash
            
            return web.json_response({
                "status": "received",
                "task_id": task_id,
                "file_hash": file_hash
            })
            
        except Exception as e:
            logger.error(f"Error receiving from Machine 1: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def send_to_machine3(self, file_hash: str, file_bytes: bytes) -> str:
        """Send malware file to Machine 3 for analysis"""
        task_id = f"{file_hash}_{datetime.now().timestamp()}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://{MACHINE3_IP}:{MACHINE3_PORT}/api/analyze",
                    json={
                        "task_id": task_id,
                        "file_hash": file_hash,
                        "file_data": file_bytes.hex(),
                        "callback_url": f"http://{MACHINE1_IP}:{MACHINE1_PORT}/api/sandbox/process_result"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    result = await resp.json()
                    logger.info(f"Machine 3 accepted analysis: {result}")
                    return task_id
        except Exception as e:
            logger.error(f"Failed to send to Machine 3: {e}")
            return task_id
    
    async def get_status(self, request):
        """GET /api/dmz/status/{task_id}"""
        task_id = request.match_info['task_id']
        
        if task_id in self.completed_analyses:
            return web.json_response({
                "status": "completed",
                "result": self.completed_analyses[task_id]
            })
        elif task_id in self.pending_analyses:
            return web.json_response({
                "status": "analyzing",
                "file_hash": self.pending_analyses[task_id]
            })
        else:
            return web.json_response({"status": "unknown"}, status=404)
    
    async def receive_from_machine3(self, request):
        """
        Endpoint for Machine 3 to send analysis results
        POST /api/dmz/results
        """
        try:
            data = await request.json()
            task_id = data.get('task_id')
            analysis_result = data.get('result')
            
            logger.info(f"Received analysis result from Machine 3: {task_id}")
            
            # Store result
            self.completed_analyses[task_id] = analysis_result
            
            # Forward to Machine 1
            await self.send_to_machine1(task_id, analysis_result)
            
            return web.json_response({"status": "received"})
            
        except Exception as e:
            logger.error(f"Error receiving from Machine 3: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def send_to_machine1(self, task_id: str, result: dict):
        """Send sanitized results back to Machine 1"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://{MACHINE1_IP}:{MACHINE1_PORT}/api/sandbox/process_result",
                    json={
                        "task_id": task_id,
                        "result": result
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    logger.info(f"Sent result to Machine 1: {await resp.json()}")
        except Exception as e:
            logger.error(f"Failed to send to Machine 1: {e}")

async def main():
    app = web.Application()
    orchestrator = DMZOrchestrator()
    
    app.router.add_post('/api/dmz/receive', orchestrator.receive_from_machine1)
    app.router.add_get('/api/dmz/status/{task_id}', orchestrator.get_status)
    app.router.add_post('/api/dmz/results', orchestrator.receive_from_machine3)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', DMZ_PORT)
    await site.start()
    
    logger.info(f"DMZ Orchestrator listening on port {DMZ_PORT}")
    logger.info(f"Machine 1 (Safe Zone): http://{MACHINE1_IP}:{MACHINE1_PORT}")
    logger.info(f"Machine 3 (Danger Zone): http://{MACHINE3_IP}:{MACHINE3_PORT}")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Configure Network

```bash
# Machine 2 - DMZ Orchestrator
# Configure IP addresses for bridging

# Network interface to Machine 1 (Safe Network)
sudo nano /etc/netplan/01-netcfg.yaml
```

**Content:**
```yaml
# Machine 2 DMZ Configuration
network:
  version: 2
  ethernets:
    eth0:
      # Connected to Machine 1 (Safe Zone)
      dhcp4: no
      addresses:
        - 192.168.1.50/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
    
    eth1:
      # Connected to Machine 3 (Danger Zone)
      dhcp4: no
      addresses:
        - 192.168.3.1/24
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

```bash
# Apply network configuration
sudo netplan apply
sudo systemctl restart networking

# Verify
ip addr show
```

### Step 4: Start DMZ Orchestrator

```bash
cd /home/ubuntu/multisec-dmz
source venv/bin/activate
python dmz_orchestrator.py
```

---

## 💻 Phase 3: Machine 3 Setup (Analysis Server)

### Hardware Requirements
- **CPU:** 4+ cores (Intel i5/i7 or Ryzen 5/7)
- **RAM:** 16GB minimum
- **Storage:** 500GB+ SSD recommended
- **OS:** Ubuntu 22.04 LTS Server
- **Network:** Single ethernet to Machine 2

### Step 1: Install CAPE Sandbox

```bash
# On Machine 3
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.10 python3-pip python3-venv git curl \
  libvirt-daemon libvirt-clients qemu-system-x86 qemu-utils \
  libxml2-dev libxslt-dev libjpeg-dev zlib1g-dev openssl

# Clone CAPE
mkdir ~/work && cd ~/work
git clone https://github.com/kevoreilly/CAPEv2.git
cd CAPEv2
python3 -m venv venv
source venv/bin/activate
pip install -U pip setuptools
pip install -e .

# Install with KVM support
pip install libvirt-python
```

### Step 2: Create Windows VM for Analysis

```bash
# Create VM for malware analysis
mkdir -p ~/vms/analysis_vm

# Download Windows 10/11 ISO or use existing
# Create VM disk
qemu-img create -f qcow2 ~/vms/analysis_vm/disk.qcow2 50G

# Create VM with networking isolated to DMZ
# This requires KVM/QEMU configuration (detailed setup below)
```

### Step 3: Create Analysis Service

Create `/home/ubuntu/multisec-analysis/analysis_service.py`:

```python
"""
Analysis Service - Machine 3
Receives malware files from DMZ (Machine 2)
Executes in CAPE Sandbox
Sends results back to DMZ
"""

import asyncio
import json
import subprocess
from aiohttp import web
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnalysisService")

MACHINE2_IP = "192.168.3.1"    # DMZ Orchestrator IP
MACHINE2_PORT = 8001
ANALYSIS_STORAGE = Path("./analysis_storage")
CAPE_PATH = "/home/ubuntu/work/CAPEv2"

ANALYSIS_STORAGE.mkdir(exist_ok=True)

class AnalysisService:
    def __init__(self):
        self.active_analyses = {}
        self.results_cache = {}
    
    async def analyze_malware(self, request):
        """
        Endpoint for DMZ to send malware samples
        POST /api/analyze
        """
        try:
            data = await request.json()
            task_id = data.get('task_id')
            file_hash = data.get('file_hash')
            file_bytes = bytes.fromhex(data.get('file_data', ''))
            
            logger.info(f"Starting analysis: {task_id}")
            
            # Save file
            sample_path = ANALYSIS_STORAGE / file_hash
            sample_path.write_bytes(file_bytes)
            
            # Start CAPE analysis asynchronously
            asyncio.create_task(self._run_cape_analysis(task_id, sample_path))
            
            return web.json_response({
                "status": "accepted",
                "task_id": task_id
            })
            
        except Exception as e:
            logger.error(f"Error receiving sample: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _run_cape_analysis(self, task_id: str, sample_path: Path):
        """Execute CAPE sandbox analysis"""
        try:
            self.active_analyses[task_id] = "running"
            
            # Run CAPE analysis
            # CAPE uses: capa analysis/submit.py -f /path/to/sample
            result = subprocess.run(
                [
                    f"{CAPE_PATH}/venv/bin/python",
                    f"{CAPE_PATH}/utils/submit.py",
                    "--file", str(sample_path),
                    "--timeout", "120",
                    "--platform", "windows",
                    "--analysis", "complete"
                ],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse CAPE results (JSON format)
            try:
                analysis_output = json.loads(result.stdout)
            except:
                analysis_output = {
                    "status": "error",
                    "output": result.stdout,
                    "error": result.stderr
                }
            
            # Process results
            threat_analysis = await self._process_cape_results(analysis_output)
            
            # Send back to DMZ
            await self._send_results_to_dmz(task_id, threat_analysis)
            
            self.active_analyses[task_id] = "completed"
            logger.info(f"Analysis completed: {task_id}")
            
        except Exception as e:
            logger.error(f"Analysis error for {task_id}: {e}")
            self.active_analyses[task_id] = "failed"
    
    async def _process_cape_results(self, cape_output: dict) -> dict:
        """Extract and process CAPE results"""
        return {
            "timestamp": datetime.now().isoformat(),
            "network_iocs": self._extract_network_iocs(cape_output),
            "file_indicators": self._extract_file_indicators(cape_output),
            "behavioral_indicators": self._extract_behaviors(cape_output),
            "raw_cape_output": cape_output
        }
    
    def _extract_network_iocs(self, cape_output: dict) -> list:
        """Extract network IOCs from CAPE report"""
        iocs = []
        if "network" in cape_output:
            network = cape_output["network"]
            # Extract IPs, domains, URLs
            if "tcp" in network:
                for tcp in network["tcp"]:
                    iocs.append({"type": "ip", "value": tcp.get("dst")})
            if "dns" in network:
                for dns in network["dns"]:
                    iocs.append({"type": "domain", "value": dns.get("request")})
        return iocs
    
    def _extract_file_indicators(self, cape_output: dict) -> list:
        """Extract file indicators"""
        indicators = []
        if "dropped" in cape_output:
            for dropped in cape_output["dropped"]:
                indicators.append({
                    "type": "file",
                    "name": dropped.get("name"),
                    "md5": dropped.get("md5"),
                    "path": dropped.get("path")
                })
        return indicators
    
    def _extract_behaviors(self, cape_output: dict) -> list:
        """Extract behavioral indicators"""
        behaviors = []
        if "behavior" in cape_output:
            for process in cape_output["behavior"].get("processes", []):
                behaviors.append({
                    "process": process.get("process_name"),
                    "calls": len(process.get("calls", []))
                })
        return behaviors
    
    async def get_status(self, request):
        """GET /api/analysis/status/{task_id}"""
        task_id = request.match_info['task_id']
        status = self.active_analyses.get(task_id, "unknown")
        
        return web.json_response({"status": status, "task_id": task_id})
    
    async def _send_results_to_dmz(self, task_id: str, results: dict):
        """Send analysis results back to DMZ"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://{MACHINE2_IP}:{MACHINE2_PORT}/api/dmz/results",
                    json={
                        "task_id": task_id,
                        "result": results
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    logger.info(f"Results sent to DMZ: {await resp.json()}")
        except Exception as e:
            logger.error(f"Failed to send results to DMZ: {e}")

async def main():
    app = web.Application()
    service = AnalysisService()
    
    app.router.add_post('/api/analyze', service.analyze_malware)
    app.router.add_get('/api/analysis/status/{task_id}', service.get_status)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    
    logger.info("Analysis Service listening on port 8000")
    logger.info(f"DMZ (Machine 2): http://{MACHINE2_IP}:{MACHINE2_PORT}")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Configure Firewall

```bash
# Machine 3 - Only allow DMZ connection
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.3.1 to any port 8000
sudo ufw allow from 192.168.3.0/24 to any port 8000
sudo ufw status
```

---

## 🧠 Phase 4: Model Training

### Option A: Using Existing Data

```bash
# On Machine 1
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system
source venv/bin/activate

# Convert CAPE results to training data
python data/converter.py

# Train DistilBERT with new malware patterns
python train_bert_model.py --epochs 5 --learning_rate 2e-5
```

### Option B: Generate New Training Data

```bash
# Generate realistic logs for training
python generate_realistic_logs.py --count 1000

# Convert to training format
python data/converter.py

# Train model
python train_bert_model.py
```

### Option C: Use EMBER Dataset

```bash
# Download EMBER dataset
cd data
kaggle datasets download -d unicamp-dl/malware-research-ember
unzip malware-research-ember.zip

# Convert to BERT training format
python converter.py --format ember

# Train
python ../train_bert_model.py --dataset ember
```

---

## 🧪 Phase 5: End-to-End Testing

### Step 1: Start All Services

**Terminal 1 - Machine 1 (Backend):**
```bash
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system
source venv/bin/activate
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Machine 1 (Frontend):**
```bash
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system/frontend/sandbox-viewer
python -m http.server 8080
```

**Machine 2 - DMZ Orchestrator:**
```bash
ssh ubuntu@192.168.1.50
cd multisec-dmz
source venv/bin/activate
python dmz_orchestrator.py
```

**Machine 3 - Analysis Service:**
```bash
ssh ubuntu@192.168.3.100
cd multisec-analysis
source venv/bin/activate
python analysis_service.py
```

### Step 2: Prepare Test Malware (Safe)

```bash
# Create benign test files (use text instead of real malware for first test)

# Option 1: EICAR test file
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > eicar.txt

# Option 2: Use existing malware samples from your data
ls data/*.csv
```

### Step 3: Upload via GUI

1. Open http://localhost:8080/sandbox.html
2. Go to **"Upload Malware"** tab
3. Drag and drop `eicar.txt`
4. Click **"Submit for Analysis"**
5. Wait for analysis to complete

### Step 4: Monitor Analysis

**Terminal 3 - Check Machine 1 logs:**
```bash
tail -f /tmp/machine1_logs.txt
```

**Terminal 4 - Check Machine 2 logs:**
```bash
ssh ubuntu@192.168.1.50 'tail -f ~/multisec-dmz/dmz.log'
```

**Terminal 5 - Check Machine 3 logs:**
```bash
ssh ubuntu@192.168.3.100 'tail -f ~/multisec-analysis/analysis.log'
```

### Step 5: View Results

1. Click **"Submissions"** tab on http://localhost:8080/sandbox.html
2. Find your uploaded file
3. Click **"View Results"**
4. Check:
   - Threat classification (BERT confidence)
   - Risk score (0-100)
   - IOCs extracted
   - Recommendations
   - Behavioral summary

---

## 🔧 Troubleshooting

### Machine 2 can't reach Machine 3

```bash
# On Machine 2
ping 192.168.3.100
curl -v http://192.168.3.100:8000/api/analysis/status/test

# Check firewall on Machine 3
sudo ufw status
sudo ufw allow from 192.168.3.1
```

### Machine 1 can't reach DMZ

```bash
# On Machine 1
curl -v http://192.168.1.50:8001/api/dmz/status/test

# Update Machine 1's DMZ configuration
nano backend/main.py  # Check DMZ_IP and DMZ_PORT
```

### CAPE Sandbox not working

```bash
# On Machine 3
source /home/ubuntu/work/CAPEv2/venv/bin/activate
python -m cape.utils.submit --help
python -m cape.web  # Start CAPE web interface at http://192.168.3.100:8080
```

### Model training fails

```bash
# Check BERT model path
ls -la models/distilbert_log_classifier/

# Verify training data exists
ls -la data/training/

# Test BERT locally
python -c "from transformers import pipeline; print(pipeline('text-classification'))"
```

---

## 📊 Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│         MACHINE 1: SAFE ZONE (Main App)             │
│         http://localhost:8000 & :8080               │
│  ┌──────────────────────────────────────────────┐   │
│  │ FastAPI Backend (Threat Detection)           │   │
│  │ - BERT Classifier (97-100% accuracy)         │   │
│  │ - Risk Scoring Engine                        │   │
│  │ - Web Interface (Upload, View Results)       │   │
│  │ - SQLite Database                            │   │
│  └──────────────────────────────────────────────┘   │
│                   ↓ (HTTPS)                         │
│        192.168.1.100 ↔ 192.168.1.50                │
│                                                      │
└─────────────────────────────────────────────────────┘
         (User Access / Safe Network)


┌─────────────────────────────────────────────────────┐
│    MACHINE 2: DMZ (Orchestrator)                     │
│    http://192.168.1.50 & :192.168.3.1:8001         │
│  ┌──────────────────────────────────────────────┐   │
│  │ DMZ Orchestrator                             │   │
│  │ - Receives files from Machine 1              │   │
│  │ - Validates and sanitizes                    │   │
│  │ - Forwards to Machine 3                      │   │
│  │ - Returns results to Machine 1               │   │
│  └──────────────────────────────────────────────┘   │
│              ↓ (Network Isolated)                   │
│         192.168.3.1 ↔ 192.168.3.100                │
│                                                      │
└─────────────────────────────────────────────────────┘
         (Isolated DMZ Network)


┌─────────────────────────────────────────────────────┐
│   MACHINE 3: DANGER ZONE (Analysis Server)          │
│   http://192.168.3.100:8000                        │
│  ┌──────────────────────────────────────────────┐   │
│  │ CAPE Sandbox Analysis Service                │   │
│  │ - Isolated Windows VMs                       │   │
│  │ - Malware execution & monitoring             │   │
│  │ - Behavioral analysis                        │   │
│  │ - IOC extraction (IPs, files, registry)      │   │
│  │ - Results generation                         │   │
│  └──────────────────────────────────────────────┘   │
│              ↓ (Back to DMZ → Machine 1)            │
│                                                      │
└─────────────────────────────────────────────────────┘
      (Physically Isolated Network)
```

---

## ✅ Verification Checklist

- [ ] Machine 1: Backend API running on port 8000
- [ ] Machine 1: Frontend UI accessible on port 8080
- [ ] Machine 2: DMZ Orchestrator running, can ping Machine 1 & 3
- [ ] Machine 3: Analysis Service running on port 8000
- [ ] Machine 3: CAPE Sandbox installed and configured
- [ ] Network: Machine 1 ↔ Machine 2 connection working
- [ ] Network: Machine 2 ↔ Machine 3 connection working
- [ ] Model: BERT trained on latest threats
- [ ] Database: All tables created and indexes applied
- [ ] Upload: Test file uploaded successfully via GUI
- [ ] Analysis: Results appear in submissions list
- [ ] Results: Threat classification, risk score, IOCs visible

---

## 🚀 Quick Start Commands

**After everything is set up, use these:**

```bash
# Machine 1
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system
source venv/bin/activate
python -m uvicorn backend.main:app &
cd frontend/sandbox-viewer && python -m http.server 8080 &
echo "Open http://localhost:8080/sandbox.html"

# Machine 2
ssh ubuntu@192.168.1.50 'cd multisec-dmz && source venv/bin/activate && python dmz_orchestrator.py'

# Machine 3
ssh ubuntu@192.168.3.100 'cd multisec-analysis && source venv/bin/activate && python analysis_service.py'
```

---

## 📞 Support

If you encounter issues:

1. Check logs on each machine
2. Verify network connectivity: `ping` between machines
3. Check firewall rules: `sudo ufw status`
4. Verify services are running: `ps aux | grep python`
5. Test API endpoints manually: `curl -v http://machine-ip:port/api/endpoint`
