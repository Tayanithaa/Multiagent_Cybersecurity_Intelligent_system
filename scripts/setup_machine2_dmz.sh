#!/bin/bash
#
# Machine 2 (DMZ Orchestrator) - Automated Setup Script
# Run this on your Raspberry Pi or old laptop
#

set -e

echo "=========================================="
echo "Machine 2 DMZ Orchestrator Setup"
echo "=========================================="
echo ""

# Get IP configuration
read -p "Enter Machine 1 IP address (Safe Zone): " MACHINE1_IP
read -p "Enter Machine 3 IP address (Danger Zone): " MACHINE3_IP
read -p "Enter this machine's IP (should be on both networks): " MACHINE2_IP

echo "Configuration:"
echo "  Machine 1 (Safe): $MACHINE1_IP:8000"
echo "  Machine 2 (This):  $MACHINE2_IP:8001"
echo "  Machine 3 (Danger): $MACHINE3_IP:8000"
echo ""

# Update system
echo "[1/6] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "[2/6] Installing dependencies..."
sudo apt install -y python3.10 python3-pip python3-venv git curl

# Create directory structure
echo "[3/6] Creating directories..."
mkdir -p ~/multisec-dmz
cd ~/multisec-dmz

# Clone or download project files
echo "[4/6] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -U pip setuptools

# Install requirements
echo "Installing Python packages..."
cat > requirements-dmz.txt << 'EOF'
aiohttp==3.9.1
aiofiles==25.1.0
pydantic==2.0.0
python-dotenv==1.0.0
EOF

pip install -r requirements-dmz.txt

# Create DMZ Orchestrator service
echo "[5/6] Creating DMZ Orchestrator service..."
cat > dmz_orchestrator.py << 'EOFPYTHON'
import asyncio
import json
import aiohttp
from aiohttp import web
from pathlib import Path
import hashlib
import logging
from datetime import datetime
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dmz.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DMZ_Orchestrator")

# Configuration from environment
MACHINE1_IP = os.getenv('MACHINE1_IP', '192.168.1.100')
MACHINE3_IP = os.getenv('MACHINE3_IP', '192.168.3.100')
MACHINE1_PORT = 8000
MACHINE3_PORT = 8000
DMZ_PORT = 8001
DMZ_STORAGE = Path("./dmz_storage")

DMZ_STORAGE.mkdir(exist_ok=True)
logger.info(f"DMZ Storage: {DMZ_STORAGE.absolute()}")

class DMZOrchestrator:
    def __init__(self):
        self.pending_analyses = {}
        self.completed_analyses = {}
        
    async def receive_from_machine1(self, request):
        """Receive malware file from Machine 1"""
        try:
            data = await request.json()
            file_hash = data.get('file_hash')
            file_bytes = bytes.fromhex(data.get('file_data', ''))
            
            logger.info(f"[DMZ] Received {len(file_bytes)} bytes from Machine 1: {file_hash}")
            
            # Store file
            temp_file = DMZ_STORAGE / file_hash
            temp_file.write_bytes(file_bytes)
            temp_file.chmod(0o444)  # Read-only
            
            # Forward to Machine 3
            task_id = await self.send_to_machine3(file_hash, file_bytes)
            self.pending_analyses[task_id] = file_hash
            
            logger.info(f"[DMZ] Forwarded to Machine 3 with task_id: {task_id}")
            
            return web.json_response({
                "status": "received",
                "task_id": task_id,
                "file_hash": file_hash
            })
            
        except Exception as e:
            logger.error(f"[DMZ] Error from Machine 1: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def send_to_machine3(self, file_hash: str, file_bytes: bytes) -> str:
        """Forward file to Machine 3 for analysis"""
        task_id = f"{file_hash}_{int(datetime.now().timestamp() * 1000)}"
        
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
                    logger.info(f"[DMZ→3] Machine 3 accepted analysis: {result}")
                    return task_id
        except asyncio.TimeoutError:
            logger.warning(f"[DMZ→3] Timeout reaching Machine 3")
            return task_id
        except Exception as e:
            logger.error(f"[DMZ→3] Failed to send to Machine 3: {e}")
            return task_id
    
    async def get_status(self, request):
        """Check analysis status"""
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
        """Receive analysis results from Machine 3"""
        try:
            data = await request.json()
            task_id = data.get('task_id')
            analysis_result = data.get('result')
            
            logger.info(f"[DMZ] Received analysis from Machine 3: {task_id}")
            
            self.completed_analyses[task_id] = analysis_result
            
            # Forward to Machine 1
            await self.send_to_machine1(task_id, analysis_result)
            
            return web.json_response({"status": "received"})
            
        except Exception as e:
            logger.error(f"[DMZ] Error from Machine 3: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def send_to_machine1(self, task_id: str, result: dict):
        """Send results back to Machine 1"""
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
                    logger.info(f"[DMZ→1] Sent result to Machine 1")
        except Exception as e:
            logger.error(f"[DMZ→1] Failed to send to Machine 1: {e}")

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
    
    logger.info("="*50)
    logger.info("DMZ Orchestrator Started")
    logger.info("="*50)
    logger.info(f"Listening on port {DMZ_PORT}")
    logger.info(f"Machine 1 (Safe Zone): http://{MACHINE1_IP}:{MACHINE1_PORT}")
    logger.info(f"Machine 3 (Danger Zone): http://{MACHINE3_IP}:{MACHINE3_PORT}")
    logger.info("="*50)
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
EOFPYTHON

# Create systemd service file
echo "[6/6] Creating systemd service..."
sudo tee /etc/systemd/system/multisec-dmz.service > /dev/null << EOF
[Unit]
Description=AI_Aztechs DMZ Orchestrator
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$(pwd)
Environment="MACHINE1_IP=$MACHINE1_IP"
Environment="MACHINE3_IP=$MACHINE3_IP"
ExecStart=$(pwd)/venv/bin/python dmz_orchestrator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Test connections:"
echo "   ping $MACHINE1_IP"
echo "   ping $MACHINE3_IP"
echo ""
echo "2. Start DMZ Orchestrator:"
echo "   cd ~/multisec-dmz"
echo "   source venv/bin/activate"
echo "   python dmz_orchestrator.py"
echo ""
echo "3. Or use systemd service:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable multisec-dmz"
echo "   sudo systemctl start multisec-dmz"
echo "   sudo systemctl status multisec-dmz"
echo ""
echo "4. Monitor logs:"
echo "   tail -f ~/multisec-dmz/dmz.log"
echo ""
