#!/bin/bash
#
# Machine 1 (Main App) - Quick Start Script
# Run this on your main application server
#

set -e

echo "=========================================="
echo "Machine 1 Main Application Setup"
echo "=========================================="
echo ""

# Configuration
read -p "Enter Machine 2 (DMZ) IP address: " DMZ_IP
read -p "Enter port for backend API (default 8000): " BACKEND_PORT
BACKEND_PORT=${BACKEND_PORT:-8000}
read -p "Enter port for frontend UI (default 8080): " FRONTEND_PORT
FRONTEND_PORT=${FRONTEND_PORT:-8080}

echo ""
echo "Configuration:"
echo "  DMZ IP: $DMZ_IP:8001"
echo "  Backend: localhost:$BACKEND_PORT"
echo "  Frontend: localhost:$FRONTEND_PORT"
echo ""

# Navigate to project directory
PROJECT_DIR="/home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system"
cd "$PROJECT_DIR"

echo "[1/4] Activating Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "[2/4] Installing/updating dependencies..."
pip install -U pip setuptools wheel
pip install -r requirements.txt

echo "[3/4] Updating backend configuration..."
# Update backend/main.py with DMZ IP
python << EOFPYTHON
import re

with open('backend/main.py', 'r') as f:
    content = f.read()

# Update DMZ_IP
content = re.sub(r'DMZ_IP\s*=\s*["\'].*?["\']', f'DMZ_IP = "{DMZ_IP}"', content)
content = re.sub(r'DMZ_PORT\s*=\s*\d+', 'DMZ_PORT = 8001', content)

with open('backend/main.py', 'w') as f:
    f.write(content)

print(f"✅ Updated backend configuration (DMZ: {DMZ_IP}:8001)")
EOFPYTHON

echo "[4/4] Initializing database..."
python << EOFPYTHON
from backend.database import Database

db = Database()
db.init_db()
print("✅ Database initialized")
EOFPYTHON

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the system, run these commands:"
echo ""
echo "=== Terminal 1: Backend API ==="
echo "cd $PROJECT_DIR"
echo "source venv/bin/activate"
echo "python -m uvicorn backend.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload"
echo ""
echo "=== Terminal 2: Frontend UI ==="
echo "cd $PROJECT_DIR/frontend/sandbox-viewer"
echo "python -m http.server $FRONTEND_PORT"
echo ""
echo "=== Then Open Browser ==="
echo "Frontend: http://localhost:$FRONTEND_PORT/sandbox.html"
echo "API Docs: http://localhost:$BACKEND_PORT/docs"
echo ""
echo "Press ENTER to start backends now..."
read

echo ""
echo "Starting Backend API..."
cd "$PROJECT_DIR"
source venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload
