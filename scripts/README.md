# 🚀 Automated Setup Scripts

This directory contains ready-to-use setup scripts for the 3-machine sandbox malware analysis system.

## 📋 Available Scripts

### 1. **setup_machine1_main.sh** - Main Application Server
Initialize and start Machine 1 (Safe Zone) with the FastAPI backend and web interface.

```bash
bash setup_machine1_main.sh
```

**What it does:**
- Sets up Python environment
- Configures backend with DMZ IP
- Initializes SQLite database
- Starts API server and frontend UI

**Requirements:**
- Run on your main application server
- Python 3.10+
- Network access to DMZ machine

---

### 2. **setup_machine2_dmz.sh** - DMZ Orchestrator
Set up Machine 2 as the DMZ orchestrator that bridges the safe and danger zones.

```bash
bash setup_machine2_dmz.sh
```

**What it does:**
- Installs async HTTP dependencies
- Creates DMZ Orchestrator service
- Sets up systemd service for auto-start
- Configures logging

**Hardware:**
- Raspberry Pi 4 (8GB) - $120, OR
- Old laptop with Linux - $0-50

**Network Requirements:**
- 2 separate network interfaces (or 1 Ethernet + WiFi)
- IP on Safe network (192.168.1.x)
- IP on Danger network (192.168.3.x)

**Example IPs:**
```
Machine 1 (Safe): 192.168.1.100
Machine 2 (DMZ):  192.168.1.50 and 192.168.3.1
Machine 3 (Danger): 192.168.3.100
```

---

### 3. **setup_machine3_analysis.sh** - Analysis Server
Deploy Machine 3 with analysis capabilities and basic CAPE sandbox framework.

```bash
bash setup_machine3_analysis.sh
```

**What it does:**
- Installs CAPE Sandbox framework
- Creates Analysis Service
- Configures firewall (only allows DMZ connections)
- Sets up systemd service

**Hardware Requirements:**
- 4+ CPU cores
- 16GB RAM minimum
- 500GB+ storage
- Ubuntu 22.04 LTS

**Network:**
- Only connected to DMZ (Machine 2)
- Firewall blocks all external connections
- Only allows port 8000 from DMZ IP (192.168.3.1)

---

### 4. **test_3machine_setup.sh** - Verification Tests
Comprehensive validation of all 3 machines and their connections.

```bash
bash test_3machine_setup.sh
```

**Tests:**
- ✅ Network connectivity (ping between machines)
- ✅ Service health (HTTP responses)
- ✅ Database integrity (tables exist)
- ✅ API endpoints (responding correctly)
- ✅ File upload workflow

**When to run:**
- After initial setup
- Before going into production
- After network changes
- Troubleshooting connectivity issues

---

### 5. **train_model.sh** - Model Training
Train BERT classifier on new malware analysis results.

```bash
bash train_model.sh
```

**Options:**
1. Quick Training (5 epochs, ~10 min)
2. Full Training (15 epochs, ~30 min)
3. Generate synthetic data first
4. Use EMBER malware dataset

**Best for:**
- Improving detection accuracy with new threats
- Learning from submitted malware samples
- Retraining after major changes
- Batch processing of analysis results

---

## 📦 Setup Sequence

### Initial Deployment (First Time)

```bash
# Step 1: Prepare Machine 1 (Main App)
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system
bash scripts/setup_machine1_main.sh

# Step 2: Prepare Machine 2 (DMZ) - on another computer
ssh ubuntu@192.168.1.50
git clone <your-repo>
bash scripts/setup_machine2_dmz.sh

# Step 3: Prepare Machine 3 (Analysis) - on isolated computer
ssh ubuntu@192.168.3.100
git clone <your-repo>
bash scripts/setup_machine3_analysis.sh

# Step 4: Verify Everything Works
bash scripts/test_3machine_setup.sh
```

### Regular Operations

```bash
# Start all services
# Terminal 1 - Machine 1
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system
source venv/bin/activate
python -m uvicorn backend.main:app --port 8000

# Terminal 2 - Machine 1 Frontend
cd /home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system/frontend/sandbox-viewer
python -m http.server 8080

# SSH to Machine 2
ssh ubuntu@192.168.1.50
cd multisec-dmz && source venv/bin/activate && python dmz_orchestrator.py

# SSH to Machine 3
ssh ubuntu@192.168.3.100
cd multisec-analysis && python analysis_service.py
```

### Model Improvement Cycle

```bash
# After collecting analysis results
bash scripts/train_model.sh

# Select option: 1 (Quick) or 2 (Full)
# Wait for training to complete
# Backend automatically reloads new model
```

---

## 🔧 Configuration

### Machine-to-Machine Communication

Each script asks for IP addresses. Use these defaults:

```
Safe Network (Machines 1 & 2):
  Machine 1: 192.168.1.100
  Machine 2: 192.168.1.50 (first interface)

Danger Network (Machines 2 & 3):
  Machine 2: 192.168.3.1 (second interface)
  Machine 3: 192.168.3.100

No internet access from Machine 3 for security
```

### Custom Configuration

Edit the scripts before running:

```bash
# Machine 2 DMZ configuration
MACHINE1_IP=192.168.1.100
MACHINE3_IP=192.168.3.100
DMZ_PORT=8001

# Machine 3 Analysis configuration
MACHINE2_IP=192.168.3.1
ANALYSIS_PORT=8000
```

---

## ⚠️ Important Notes

### Security

1. **Machine 3 is isolated** - Do NOT add internet access
2. **Firewall enabled** - Only allows DMZ connections
3. **Read-only storage** - Malware can't modify files
4. **No execution** - Files never execute on Machine 1

### Network Setup

1. **Physical separation required** - Use different WiFi/Ethernet
2. **Network isolation optional** - Can use VLANs instead
3. **One-way communication** - Machine 3 never initiates to other machines
4. **Firewall rules** - Automatically configured by scripts

### Common Issues

```bash
# "Machine 2 can't reach Machine 3"
# Check on Machine 3:
sudo ufw status
ping 192.168.3.1

# "Machine 1 can't reach DMZ"
# Check Machine 2 is running:
ps aux | grep dmz_orchestrator

# "API returning errors"
# Check logs:
tail -f dmz.log              # Machine 2
tail -f analysis.log         # Machine 3
```

---

## 🚀 Using with systemd

The setup scripts create systemd services for auto-start:

```bash
# Enable auto-start on Machine 2
sudo systemctl enable multisec-dmz
sudo systemctl start multisec-dmz
sudo systemctl status multisec-dmz

# Enable auto-start on Machine 3
sudo systemctl enable multisec-analysis
sudo systemctl start multisec-analysis
sudo systemctl status multisec-analysis

# View logs
sudo journalctl -u multisec-dmz -f
sudo journalctl -u multisec-analysis -f
```

---

## 📊 Monitoring

### Check All Services

```bash
# Machine 1
ps aux | grep uvicorn
curl http://localhost:8000/docs

# Machine 2
ssh ubuntu@192.168.1.50 'ps aux | grep dmz'
ssh ubuntu@192.168.1.50 'curl http://localhost:8001/api/dmz/status/test'

# Machine 3
ssh ubuntu@192.168.3.100 'ps aux | grep analysis'
ssh ubuntu@192.168.3.100 'curl http://localhost:8000/api/analysis/status/test'
```

### View Logs

```bash
# Machine 1
tail -f backend/logs/main.log

# Machine 2
ssh ubuntu@192.168.1.50 'tail -f ~/multisec-dmz/dmz.log'

# Machine 3
ssh ubuntu@192.168.3.100 'tail -f ~/multisec-analysis/analysis.log'
```

---

## ✅ Verification Checklist

After running setup scripts:

- [ ] Machine 1: http://localhost:8080/sandbox.html loads
- [ ] Machine 1: http://localhost:8000/docs shows API
- [ ] Machine 2: `curl http://MACHINE2_IP:8001/api/dmz/status/test` responds
- [ ] Machine 3: `curl http://MACHINE3_IP:8000/api/analysis/status/test` responds
- [ ] Network: All machines can ping each other
- [ ] Firewall: Machine 3 only allows DMZ IP
- [ ] Database: All 4 tables exist on Machine 1
- [ ] Test: Run `bash test_3machine_setup.sh` and see ✅ marks

---

## 🎯 Next Steps

1. **Immediate:** Run setup scripts in order (1, 2, 3, then verify)
2. **Test:** Use verification script to confirm connectivity
3. **Train:** Upload malware samples and train model
4. **Monitor:** Keep logs open during analysis
5. **Refine:** Adjust firewall rules as needed

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check firewall and service status |
| Timeout errors | Verify network connectivity with ping |
| Database errors | Run setup script again to reinitialize |
| Model training fails | Check training data exists in `data/` |
| Settings not updating | Restart services after configuration changes |

---

## 📞 Support

For detailed documentation, see:
- `docs/COMPLETE_SETUP_GUIDE.md` - Full setup guide
- `docs/SANDBOX_IMPLEMENTATION.md` - Implementation details
- `README.md` - Project overview

---

**Last Updated:** February 18, 2026  
**Status:** ✅ Production Ready
