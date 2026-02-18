#!/bin/bash
#
# End-to-End Testing Script
# Tests connectivity and functionality of all 3 machines
#

set -e

echo "=========================================="
echo "3-Machine Sandbox Setup - Verification"
echo "=========================================="
echo ""

# Get IPs
read -p "Enter Machine 1 IP (or localhost): " MACHINE1_IP
MACHINE1_IP=${MACHINE1_IP:-localhost}
read -p "Enter Machine 2 (DMZ) IP: " MACHINE2_IP
read -p "Enter Machine 3 (Analysis) IP: " MACHINE3_IP

MACHINE1_PORT=8000
MACHINE2_PORT=8001
MACHINE3_PORT=8000

echo ""
echo "Configuration:"
echo "  Machine 1: http://$MACHINE1_IP:$MACHINE1_PORT"
echo "  Machine 2: http://$MACHINE2_IP:$MACHINE2_PORT"
echo "  Machine 3: http://$MACHINE3_IP:$MACHINE3_PORT"
echo ""

# Test 1: Network Connectivity
echo "================================"
echo "TEST 1: Network Connectivity"
echo "================================"

test_ping() {
    local ip=$1
    local name=$2
    if ping -c 1 "$ip" &> /dev/null; then
        echo "✅ $name ($ip) - Reachable"
        return 0
    else
        echo "❌ $name ($ip) - Not reachable"
        return 1
    fi
}

test_ping "$MACHINE1_IP" "Machine 1"
test_ping "$MACHINE2_IP" "Machine 2 (DMZ)"
test_ping "$MACHINE3_IP" "Machine 3 (Analysis)"

echo ""
echo "================================"
echo "TEST 2: Service Health"
echo "================================"

test_service() {
    local url=$1
    local name=$2
    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $name - OK"
        return 0
    else
        echo "❌ $name - Not responding"
        return 1
    fi
}

test_service "http://$MACHINE1_IP:$MACHINE1_PORT/docs" "Machine 1 API"
test_service "http://$MACHINE2_IP:$MACHINE2_PORT/api/dmz/status/test" "Machine 2 DMZ"
test_service "http://$MACHINE3_IP:$MACHINE3_PORT/api/analysis/status/test" "Machine 3 Analysis"

echo ""
echo "================================"
echo "TEST 3: Database Integrity"
echo "================================"

python3 << EOFPYTHON
import sys
sys.path.insert(0, '/home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system')

try:
    from backend.database import Database
    
    db = Database()
    
    tables = ['incidents', 'malware_submissions', 'malware_analysis', 'learned_patterns']
    
    for table in tables:
        cursor = db.conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            print(f"✅ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' missing")
    
except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)
EOFPYTHON

echo ""
echo "================================"
echo "TEST 4: API Endpoints"
echo "================================"

# Test Machine 1 endpoints
echo "Testing Machine 1 endpoints:"
curl -s -X GET "http://$MACHINE1_IP:$MACHINE1_PORT/api/sandbox/stats" | python3 -m json.tool > /dev/null && echo "✅ GET /api/sandbox/stats" || echo "❌ GET /api/sandbox/stats"
curl -s -X GET "http://$MACHINE1_IP:$MACHINE1_PORT/api/sandbox/list" | python3 -m json.tool > /dev/null && echo "✅ GET /api/sandbox/list" || echo "❌ GET /api/sandbox/list"

# Test Machine 2 DMZ endpoint
echo ""
echo "Testing Machine 2 endpoints:"
curl -s -X GET "http://$MACHINE2_IP:$MACHINE2_PORT/api/dmz/status/test" | python3 -m json.tool > /dev/null && echo "✅ GET /api/dmz/status/{task_id}" || echo "❌ GET /api/dmz/status/{task_id}"

# Test Machine 3 Analysis endpoint
echo ""
echo "Testing Machine 3 endpoints:"
curl -s -X GET "http://$MACHINE3_IP:$MACHINE3_PORT/api/analysis/status/test" | python3 -m json.tool > /dev/null && echo "✅ GET /api/analysis/status/{task_id}" || echo "❌ GET /api/analysis/status/{task_id}"

echo ""
echo "================================"
echo "TEST 5: File Upload to Sandbox"
echo "================================"

# Create test file
TEST_FILE="/tmp/test_malware.txt"
echo "This is a safe test file" > "$TEST_FILE"

# Calculate SHA256
FILE_HASH=$(sha256sum "$TEST_FILE" | cut -d' ' -f1)
echo "Test file SHA256: $FILE_HASH"

# Upload to Machine 1
echo ""
echo "Uploading test file to Machine 1..."

curl -s -X POST "http://$MACHINE1_IP:$MACHINE1_PORT/api/sandbox/submit" \
  -H "Content-Type: application/json" \
  -d "{
    \"file_hash\": \"$FILE_HASH\",
    \"filename\": \"test_malware.txt\",
    \"file_type\": \"text\"
  }" | python3 -m json.tool

echo ""
echo "Checking submissions list..."
curl -s -X GET "http://$MACHINE1_IP:$MACHINE1_PORT/api/sandbox/list" | python3 -m json.tool | head -20

echo ""
echo "================================"
echo "VERIFICATION COMPLETE"
echo "================================"
echo ""
echo "✅ All 3-machine tests completed"
echo ""
echo "Next steps:"
echo "1. Open http://$MACHINE1_IP:8080/sandbox.html in browser"
echo "2. Go to 'Upload Malware' tab"
echo "3. Drag and drop a test file"
echo "4. Monitor logs on each machine:"
echo "   - Machine 2: tail -f dmz.log"
echo "   - Machine 3: tail -f analysis.log"
echo ""
