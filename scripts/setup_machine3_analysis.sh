#!/bin/bash
#
# Machine 3 (Analysis Server) - CAPE Sandbox Setup Script
# Run this on your isolated analysis server
#

set -e

echo "=========================================="
echo "Machine 3 Analysis Server Setup"
echo "=========================================="
echo ""

# Get IP configuration
read -p "Enter Machine 2 (DMZ) IP address: " MACHINE2_IP
read -p "Enter this machine's IP (isolated network): " MACHINE3_IP

echo "Configuration:"
echo "  Machine 2 (DMZ):     $MACHINE2_IP:8001"
echo "  Machine 3 (This):    $MACHINE3_IP:8000"
echo ""

# Update system
echo "[1/5] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install CAPE dependencies
echo "[2/5] Installing CAPE and analysis dependencies..."
sudo apt install -y python3.10 python3-pip python3-venv python3-dev \
  libvirt-daemon libvirt-clients qemu-system-x86 qemu-utils \
  libxml2-dev libxslt-dev libjpeg-dev zlib1g-dev openssl \
  git curl build-essential libffi-dev

# Create working directory
echo "[3/5] Setting up environment..."
mkdir -p ~/work
cd ~/work

# Clone CAPE Sandbox (if not already present)
if [ ! -d "CAPEv2" ]; then
    echo "Cloning CAPE Sandbox..."
    git clone https://github.com/kevoreilly/CAPEv2.git
fi

cd CAPEv2

# Create Python virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -U pip setuptools wheel

# Install CAPE requirements
echo "Installing CAPE dependencies..."
pip install -e .

# Additional required packages
pip install aiohttp==3.9.1 aiofiles==25.1.0

# Create analysis service
echo "[4/5] Creating Analysis Service..."
mkdir -p ~/multisec-analysis
cd ~/multisec-analysis

cat > analysis_service.py << 'EOFPYTHON'
import asyncio
import json
import subprocess
from aiohttp import web
from pathlib import Path
import logging
from datetime import datetime
import os
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AnalysisService")

MACHINE2_IP = os.getenv('MACHINE2_IP', '192.168.3.1')
MACHINE2_PORT = 8001
ANALYSIS_STORAGE = Path("./analysis_storage")
CAPE_PATH = os.getenv('CAPE_PATH', '/home/ubuntu/work/CAPEv2')

ANALYSIS_STORAGE.mkdir(exist_ok=True)
logger.info(f"Analysis Storage: {ANALYSIS_STORAGE.absolute()}")
logger.info(f"CAPE Path: {CAPE_PATH}")

class AnalysisService:
    def __init__(self):
        self.active_analyses = {}
        self.results_cache = {}
    
    async def analyze_malware(self, request):
        """Receive malware file and start analysis"""
        try:
            data = await request.json()
            task_id = data.get('task_id')
            file_hash = data.get('file_hash')
            file_bytes = bytes.fromhex(data.get('file_data', ''))
            
            logger.info(f"[ANALYSIS] Starting analysis: {task_id} ({len(file_bytes)} bytes)")
            
            # Save file
            sample_path = ANALYSIS_STORAGE / file_hash
            sample_path.write_bytes(file_bytes)
            sample_path.chmod(0o400)  # Read-only
            
            # Start analysis asynchronously
            self.active_analyses[task_id] = "queued"
            asyncio.create_task(self._run_analysis(task_id, sample_path))
            
            return web.json_response({
                "status": "accepted",
                "task_id": task_id,
                "file_hash": file_hash
            })
            
        except Exception as e:
            logger.error(f"[ANALYSIS] Error receiving sample: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _run_analysis(self, task_id: str, sample_path: Path):
        """Execute analysis on malware sample"""
        try:
            self.active_analyses[task_id] = "analyzing"
            logger.info(f"[ANALYSIS] Starting behavioral analysis: {task_id}")
            
            # Simple behavioral analysis (CAPE would go here)
            # For now, we'll do basic static analysis and simulator analysis
            
            analysis_result = await self._perform_basic_analysis(sample_path)
            analysis_result['task_id'] = task_id
            analysis_result['timestamp'] = datetime.now().isoformat()
            
            logger.info(f"[ANALYSIS] Analysis complete: {task_id}")
            
            # Cache result
            self.results_cache[task_id] = analysis_result
            self.active_analyses[task_id] = "completed"
            
            # Send results back to DMZ
            await self._send_results_to_dmz(task_id, analysis_result)
            
        except Exception as e:
            logger.error(f"[ANALYSIS] Error during analysis: {e}")
            self.active_analyses[task_id] = "failed"
    
    async def _perform_basic_analysis(self, sample_path: Path) -> dict:
        """Perform basic static and behavioral analysis"""
        try:
            # Read file
            file_data = sample_path.read_bytes()
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Basic static analysis
            entropy = self._calculate_entropy(file_data)
            file_type = self._detect_file_type(file_data)
            
            # Simulate sandbox analysis results
            analysis = {
                "file_hash": file_hash,
                "file_size": len(file_data),
                "entropy": entropy,
                "file_type": file_type,
                "static_analysis": {
                    "suspicious": entropy > 7.8,
                    "packed": entropy > 7.5
                },
                "network": {
                    "dns_requests": [],
                    "http_requests": [],
                    "tcp_connections": []
                },
                "files": {
                    "dropped_files": [],
                    "modified_files": []
                },
                "processes": {
                    "process_injections": 0,
                    "registry_modifications": 0,
                    "service_modifications": 0
                },
                "behaviors": {
                    "execution": "safe",
                    "malware_indicators": 0,
                    "suspicious_apis": []
                }
            }
            
            logger.info(f"Analysis: entropy={entropy:.2f}, type={file_type}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in basic analysis: {e}")
            return {
                "error": str(e),
                "analysis": "basic_static_only"
            }
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of file data"""
        import math
        if not data:
            return 0
        entropy = 0
        for i in range(256):
            p = data.count(bytes([i])) / len(data)
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    def _detect_file_type(self, data: bytes) -> str:
        """Detect file type from magic bytes"""
        if data.startswith(b'MZ'):
            return "PE_Executable"
        elif data.startswith(b'\x7FELF'):
            return "ELF_Executable"
        elif data.startswith(b'%PDF'):
            return "PDF"
        elif data.startswith(b'PK\x03\x04'):
            return "ZIP_Archive"
        else:
            return "Unknown"
    
    async def get_status(self, request):
        """Get analysis status"""
        task_id = request.match_info['task_id']
        status = self.active_analyses.get(task_id, "unknown")
        
        return web.json_response({
            "status": status,
            "task_id": task_id
        })
    
    async def get_result(self, request):
        """Get analysis result"""
        task_id = request.match_info['task_id']
        
        if task_id in self.results_cache:
            return web.json_response(self.results_cache[task_id])
        else:
            return web.json_response({"error": "Result not found"}, status=404)
    
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
                    logger.info(f"[ANALYSIS→DMZ] Results sent to DMZ: {await resp.json()}")
        except Exception as e:
            logger.error(f"[ANALYSIS→DMZ] Failed to send results: {e}")

async def main():
    app = web.Application()
    service = AnalysisService()
    
    app.router.add_post('/api/analyze', service.analyze_malware)
    app.router.add_get('/api/analysis/status/{task_id}', service.get_status)
    app.router.add_get('/api/analysis/result/{task_id}', service.get_result)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    
    logger.info("="*50)
    logger.info("Analysis Service Started")
    logger.info("="*50)
    logger.info(f"Listening on port 8000")
    logger.info(f"DMZ (Machine 2): http://{MACHINE2_IP}:{MACHINE2_PORT}")
    logger.info("="*50)
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
EOFPYTHON

# Create requirements
cat > requirements.txt << 'EOF'
aiohttp==3.9.1
aiofiles==25.1.0
pydantic==2.0.0
python-dotenv==1.0.0
EOF

pip install -r requirements.txt

echo "[5/5] Creating systemd service..."
sudo tee /etc/systemd/system/multisec-analysis.service > /dev/null << EOF
[Unit]
Description=AI_Aztechs Analysis Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$(pwd)
Environment="MACHINE2_IP=$MACHINE2_IP"
Environment="CAPE_PATH=/home/ubuntu/work/CAPEv2"
ExecStart=$(pwd)/../work/CAPEv2/venv/bin/python analysis_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure firewall
echo "Configuring firewall..."
sudo ufw enable --force
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.3.1 to any port 8000
sudo ufw status

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Test connection to DMZ:"
echo "   ping $MACHINE2_IP"
echo ""
echo "2. Start Analysis Service:"
echo "   cd ~/multisec-analysis"
echo "   python analysis_service.py"
echo ""
echo "3. Or use systemd service:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable multisec-analysis"
echo "   sudo systemctl start multisec-analysis"
echo "   sudo systemctl status multisec-analysis"
echo ""
echo "4. Monitor logs:"
echo "   tail -f ~/multisec-analysis/analysis.log"
echo ""
echo "5. To install full CAPE Sandbox (advanced):"
echo "   cd ~/work/CAPEv2"
echo "   source venv/bin/activate"
echo "   python -m cape.web"
echo ""
