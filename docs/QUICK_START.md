# 🚀 Quick Start: 3-Machine Sandbox Setup

**Time Required:** 2-4 hours  
**Difficulty:** Intermediate  
**Hardware:** 3 computers with Linux (or 1 computer with VMs)

---

## 🎯 What You'll Have After This

A physically isolated malware analysis system:
- **Machine 1** (Safe): Your main app with web upload interface
- **Machine 2** (DMZ): Orchestrator between safe and danger zones
- **Machine 3** (Isolated): Sandbox analysis server

```
User Browser
     ↓
[Machine 1: Web UI] ← (Upload malware)
     ↓
[Machine 2: DMZ] ← (Forward & sanitize)
     ↓
[Machine 3: CAPE] ← (Execute & analyze)
     ↓
Results → Back to Machine 1
```

---

## 📋 Before You Start

### Hardware Needed

**Option A: 3 Separate Computers** (Best Security)
- Computer 1: Your current Linux system ✅
- Computer 2: Raspberry Pi 4 (8GB) - ~$120 or old laptop
- Computer 3: Desktop with 16GB RAM, 500GB storage - $200-400

**Option B: Single Computer with VMs** (Quick Testing)
- 3 virtual machines (16GB RAM total)
- Ubuntu 22.04 LTS on each

**Option C: Hybrid** (Medium)
- Physical Machine 1 + 2 VMs for 2 & 3

### Network Setup Needed

- 3 separate network segments (or VLANs)
- Router or network switch (for physical)
- No internet access to Machine 3

---

## ⚡ 5-Minute Quick Start (Testing)

### On Machine 1 (Your Current System)

```bash
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system
source venv/bin/activate

# Test if everything works locally
python test_sandbox_implementation.py
```

Expected output: All ✅ PASSED

```bash
# Start backend
python -m uvicorn backend.main:app --port 8000 &

# Start frontend (new terminal)
cd frontend/sandbox-viewer
python -m http.server 8080
```

Open browser: **http://localhost:8080/sandbox.html**

✅ You can now upload files and see them in the submissions list!

---

## 🔧 Complete 3-Machine Setup

### Phase 1: Machine 1 (Already Done ✅)

On your current system:
```bash
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system
bash scripts/setup_machine1_main.sh
```

✅ Continues to run in background

---

### Phase 2: Machine 2 (DMZ Orchestrator) - 30 minutes

**Buy or repurpose:**
- Raspberry Pi 4 (8GB) - $120, OR
- Old laptop with Linux

**On Machine 2:**

```bash
# Download and run setup
git clone <your-repo> multisec-dmz
cd multisec-dmz
bash scripts/setup_machine2_dmz.sh

# Answer the prompts:
# - Machine 1 IP: 192.168.1.100 (your main computer)
# - Machine 3 IP: 192.168.3.100 (analysis server)
```

**Verify:**
```bash
tail -f dmz.log
# Should show: "DMZ Orchestrator Started"
```

✅ Machine 2 ready

---

### Phase 3: Machine 3 (Analysis Server) - 1 hour

**Buy or repurpose:**
- Used desktop - $200-400
- Must have: 4+ cores, 16GB RAM, 500GB storage

**On Machine 3:**

```bash
# Download and run setup
git clone <your-repo> multisec-analysis
cd multisec-analysis
bash scripts/setup_machine3_analysis.sh

# Answer the prompts:
# - Machine 2 IP: 192.168.3.1 (DMZ)
```

**Verify:**
```bash
tail -f analysis.log
# Should show: "Analysis Service Started"
```

✅ Machine 3 ready

---

### Phase 4: Test Integration - 10 minutes

**On Machine 1:**

```bash
bash scripts/test_3machine_setup.sh

# Answer prompts:
# Machine 1: localhost
# Machine 2: 192.168.1.50
# Machine 3: 192.168.3.100
```

Expected output:
```
✅ Machine 1 (Safe Zone) - Reachable
✅ Machine 2 (DMZ) - Reachable
✅ Machine 3 (Analysis Server) - Reachable
✅ Machine 1 API - OK
✅ Machine 2 DMZ - OK
✅ Machine 3 Analysis - OK
✅ Database tables exist
✅ All endpoints responding
```

✅ All machines connected!

---

## 🧠 Train Your Model

The system learns from uploaded malware:

```bash
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system

# Option 1: Quick training (10 minutes)
bash scripts/train_model.sh
# Choose: 1 (Quick Training)

# Option 2: Full training (30 minutes)
bash scripts/train_model.sh
# Choose: 2 (Full Training)

# Option 3: Use EMBER dataset
bash scripts/train_model.sh
# Choose: 4 (Use EMBER Dataset)
```

The model automatically reloads after training.

---

## 🎮 Upload Malware & Analyze

### Method 1: Web Interface (Easiest)

1. Open http://localhost:8080/sandbox.html
2. Click "Upload Malware" tab
3. Drag and drop a test file (or use EICAR test file)
4. Click "Submit for Analysis"

### Create Safe Test File

```bash
# EICAR test file (detected by all antivirus)
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > eicar.txt

# Or use existing samples
ls /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system/data/*.csv
```

### Check Results

1. Go to "Submissions" tab
2. Click on your uploaded file
3. View:
   - Threat classification
   - Risk score (0-100)
   - IOCs (network, files, registry)
   - Recommendations

---

## 📊 Monitor Everything

### Open 3 Terminals

**Terminal 1: Machine 1 Logs**
```bash
tail -f /tmp/backend.log
```

**Terminal 2: Machine 2 Logs** (SSH into it)
```bash
ssh ubuntu@192.168.1.50
tail -f ~/multisec-dmz/dmz.log
```

**Terminal 3: Machine 3 Logs** (SSH into it)
```bash
ssh ubuntu@192.168.3.100
tail -f ~/multisec-analysis/analysis.log
```

### Track What Happens

When you upload a file:

1. **Machine 1 logs:**
   ```
   File uploaded: file_hash_xyz
   Sending to DMZ...
   ```

2. **Machine 2 logs:**
   ```
   Received from Machine 1: file_hash_xyz
   Forwarding to Machine 3...
   ```

3. **Machine 3 logs:**
   ```
   Analysis started: file_hash_xyz
   Analysis complete
   Sending results to DMZ...
   ```

4. **Back to Machine 1:**
   ```
   Received results from DMZ
   Processing with BERT classifier
   Risk score calculated
   ```

---

## ✅ Verification Checklist

After each phase, verify:

### After Phase 1 (Machine 1)
- [ ] http://localhost:8080/sandbox.html loads
- [ ] http://localhost:8000/docs shows API
- [ ] Can upload test file locally
- [ ] Test shown in submissions

### After Phase 2 (Machine 2)
- [ ] `ping 192.168.1.50` works
- [ ] `curl http://192.168.1.50:8001/api/dmz/status/test` responds
- [ ] `tail -f dmz.log` shows no errors

### After Phase 3 (Machine 3)
- [ ] `ping 192.168.3.100` works
- [ ] `curl http://192.168.3.100:8000/api/analysis/status/test` responds
- [ ] `tail -f analysis.log` shows no errors
- [ ] Machine 3 firewall only allows DMZ: `sudo ufw status`

### After Phase 4 (Integration Test)
- [ ] `bash scripts/test_3machine_setup.sh` returns all ✅
- [ ] Upload test file → appears in all 3 logs
- [ ] Results visible in Machine 1 submissions

---

## 🚨 Troubleshooting

### "Connection refused"

```bash
# Check services running
ps aux | grep python

# Check firewall
sudo ufw status

# On Machine 3: Firewall should be
sudo ufw default deny incoming
sudo ufw allow from 192.168.3.1 to any port 8000
```

### "No module named..."

```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### "Machine 1 can't reach DMZ"

```bash
# Check IP configuration
ifconfig  # or ip addr

# Test connection
ping 192.168.1.50
curl -v http://192.168.1.50:8001/

# Check Machine 2 is running
ssh ubuntu@192.168.1.50 'ps aux | grep dmz'
```

### "Analysis not completing"

```bash
# Check Machine 3 logs
ssh ubuntu@192.168.3.100 'tail -f ~/multisec-analysis/analysis.log'

# Verify network between 2 & 3
ssh ubuntu@192.168.1.50 'ping 192.168.3.100'
```

---

## 📈 Next Steps After Setup

1. **Collect Real Malware Data**
   - Upload samples from your organization
   - API or manual uploads

2. **Train Model on Your Data**
   ```bash
   bash scripts/train_model.sh
   ```

3. **Integrate with Your SOC**
   - Use `/api/sandbox/submit` endpoint
   - Parse results in your dashboards

4. **Scale to Multiple Servers**
   - Add more Machine 3 instances
   - Load balance with M2 orchestrator

5. **Monitor & Improve**
   - Check learned patterns
   - Retrain monthly with new threats

---

## 🔐 Security Notes

1. **Machine 3 is isolated** - No internet access intentional
2. **Files never execute on M1** - SHA256 hashed, stored read-only
3. **Firewall blocks unauthorized access** - Only DMZ can reach M3
4. **One-way communication** - M3 can't initiate connections
5. **Logs monitored** - All activity tracked

---

## 📞 Quick Commands Reference

```bash
# Start all services
# Machine 1
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system
source venv/bin/activate
python -m uvicorn backend.main:app --port 8000

# Machine 2 (remote)
ssh ubuntu@192.168.1.50
cd multisec-dmz && source venv/bin/activate && python dmz_orchestrator.py

# Machine 3 (remote)
ssh ubuntu@192.168.3.100
cd multisec-analysis && python analysis_service.py

# Check status
curl http://localhost:8000/docs
curl http://192.168.1.50:8001/api/dmz/status/test
curl http://192.168.3.100:8000/api/analysis/status/test

# Train model
bash /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system/scripts/train_model.sh

# Test integration
bash /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system/scripts/test_3machine_setup.sh
```

---

## ⏱️ Timeline

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Machine 1 Setup | ✅ Done | Complete |
| 2 | Buy Machine 2 | 1-2 days | Pending |
| 2 | Setup Machine 2 | 30 min | Ready to run |
| 3 | Buy Machine 3 | 1-2 days | Pending |
| 3 | Setup Machine 3 | 1 hour | Ready to run |
| 4 | Test Integration | 10 min | Quick check |
| 5 | Train Model | 10-30 min | Regular task |
| 6 | Start Using | Immediate! | Begin uploads |

---

**Status:** ✅ Ready to Deploy  
**Next Action:** Get hardware for Machines 2 & 3, then run setup scripts
