# Deployment Guide - Multi-Agent SOC Dashboard

## Quick Start (Local Access)

### 1. Start Backend
```bash
cd /path/to/Multiagent_Cybersecurity_Intelligent_system
source venv/bin/activate
python -m uvicorn backend.main:app --reload --port 8000
```

### 2. Start Frontend
```bash
cd frontend
python3 -m http.server 8080 --bind 0.0.0.0
```

### 3. Access
Open browser to `http://localhost:8080`

---

## Remote Access (Network/Mobile/Port Forwarding)

### Prerequisites
- Backend and frontend running on a server
- Server has a local IP (e.g., `192.168.1.100`)
- Router configured for port forwarding (if accessing from outside LAN)

### 1. Start Backend with Network Binding

**⚠️ CRITICAL:** Use `--host 0.0.0.0` to allow external connections

```bash
source venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Startup validation behavior (fail-fast):**
- Backend validates all required model artifacts at startup and refuses to start if any are missing/corrupt.
- Required model folders:
    - `models/distilbert_log_classifier`
    - `models/correlation_roberta`
    - `models/ti_enrichment_bert`
    - `models/response_albert`
- Each folder should contain Hugging Face artifacts (`config.json`, tokenizer files, weights) plus `metadata.json`.

**Verify backend is accessible:**
```bash
# Check it's listening on all interfaces (0.0.0.0:8000), not just localhost (127.0.0.1:8000)
netstat -tulnp | grep 8000
# Should show: tcp  0.0.0.0:8000  0.0.0.0:*  LISTEN

# Test locally
curl http://localhost:8000/
# Should return: {"status":"online","service":"Multi-Agent SOC API",...}
```

### 2. Start Frontend
```bash
cd frontend
python3 -m http.server 8080 --bind 0.0.0.0
```

### 3. Configure Firewall

Allow incoming connections on ports 8000 and 8080:

**Ubuntu/Debian (UFW):**
```bash
sudo ufw allow 8000/tcp
sudo ufw allow 8080/tcp
sudo ufw reload
```

**CentOS/RHEL (firewalld):**
```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

**Windows:**
```powershell
New-NetFirewallRule -DisplayName "SOC Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "SOC Frontend" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

### 4. Access from Remote Device

**From devices on the same network (LAN):**
```
http://192.168.1.100:8080
```
(Replace `192.168.1.100` with your server's actual IP)

**From internet (requires port forwarding):**
```
http://your-public-ip:8080
```

---

## How Frontend Connects to Backend

The frontend automatically detects the backend URL:

```javascript
const API_BASE = `http://${window.location.hostname}:8000`;
```

**Examples:**

| Browser URL | Frontend Connects To |
|------------|---------------------|
| `http://localhost:8080` | `http://localhost:8000` |
| `http://192.168.1.100:8080` | `http://192.168.1.100:8000` |
| `http://myserver.com:8080` | `http://myserver.com:8000` |

This means:
- ✅ Works on localhost automatically
- ✅ Works on LAN/remote IP automatically
- ✅ No configuration needed when switching environments
- ⚠️ Backend MUST be on same host as frontend (different port)

---

## Troubleshooting

### Error: "Backend not available. Please start the FastAPI server."

**Symptoms:**
- Frontend loads but shows error notification
- Browser console shows `fetch` errors to `http://...:8000`

**Common Causes & Fixes:**

#### 1. Backend listening on localhost only
```bash
# Check what interface backend is bound to
netstat -tulnp | grep 8000

# ❌ Wrong (only localhost):
# tcp  127.0.0.1:8000  0.0.0.0:*  LISTEN

# ✅ Correct (all interfaces):
# tcp  0.0.0.0:8000    0.0.0.0:*  LISTEN
```

**Fix:** Restart backend with `--host 0.0.0.0`
```bash
# Kill the old process
ps aux | grep uvicorn
kill [PID]

# Restart correctly
source venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Firewall blocking port 8000
```bash
# Test if port is reachable from another device
curl http://your-server-ip:8000/

# If timeout/connection refused, check firewall
sudo ufw status
sudo ufw allow 8000/tcp
```

#### 3. Browser cache (old configuration)
- **Hard refresh:** Ctrl+Shift+R (Chrome/Firefox) or Cmd+Shift+R (Mac)
- **Clear cache:** Browser settings → Clear browsing data → Cached files
- **Incognito mode:** Test in private/incognito window

#### 4. CORS issues
Check backend console for CORS errors. The backend should have:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Port Forwarding Setup

### Router Configuration

1. **Access router admin panel** (usually `192.168.1.1` or `192.168.0.1`)
2. **Find Port Forwarding section** (may be under "Advanced", "NAT", "Virtual Server")
3. **Add rules:**

| Service Name | External Port | Internal IP | Internal Port | Protocol |
|-------------|---------------|-------------|---------------|----------|
| SOC Frontend | 8080 | 192.168.1.100 | 8080 | TCP |
| SOC Backend | 8000 | 192.168.1.100 | 8000 | TCP |

4. **Save and reboot router**

### Find Your Public IP
```bash
curl ifconfig.me
# or
curl icanhazip.com
```

### Test External Access
From a device outside your network (e.g., mobile data):
```
http://[your-public-ip]:8080
```

---

## Production Deployment

### Using systemd (Linux)

Create service file: `/etc/systemd/system/soc-backend.service`

```ini
[Unit]
Description=Multi-Agent SOC Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/soc-dashboard
Environment="PATH=/opt/soc-dashboard/venv/bin"
ExecStart=/opt/soc-dashboard/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable soc-backend
sudo systemctl start soc-backend
sudo systemctl status soc-backend
```

### Using Nginx (Reverse Proxy)

**Benefits:**
- SSL/TLS termination (HTTPS)
- Better performance
- Standard ports (80/443)

**Config:** `/etc/nginx/sites-available/soc-dashboard`

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /opt/soc-dashboard/frontend;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Update frontend API_BASE:**
```javascript
const API_BASE = `${window.location.origin}/api`;
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/soc-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Performance Optimization

### Backend Workers
For production, use multiple workers:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Number of workers = `(2 × CPU cores) + 1`

### GPU Acceleration
If using GPU for BERT inference:
```bash
# Verify GPU available
nvidia-smi

# Backend will auto-detect and use GPU
# Check logs for: "Using device: cuda"
```

### Rate Limiting
Add rate limiting to prevent abuse:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/upload")
@limiter.limit("10/minute")
async def upload_file(...):
    ...
```

---

## Security Considerations

### Production Checklist

- [ ] Change CORS `allow_origins=["*"]` to specific domain
- [ ] Enable HTTPS (use Let's Encrypt / certbot)
- [ ] Add authentication (API keys or OAuth)
- [ ] Use environment variables for secrets (not hardcoded)
- [ ] Enable rate limiting
- [ ] Configure proper logging (not console output)
- [ ] Use process manager (systemd, supervisor)
- [ ] Regular security updates
- [ ] Monitor for anomalies

### HTTPS with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx
```

### Environment Variables
```bash
# .env file
API_SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/socdb
ALLOWED_ORIGINS=https://soc.yourcompany.com

# Load in backend/main.py
from dotenv import load_dotenv
import os
load_dotenv()
```

---

## Monitoring & Logs

### View Backend Logs
```bash
# If running with systemd
sudo journalctl -u soc-backend -f

# If running manually
# Logs appear in terminal
```

### Health Check Endpoints
```bash
# Backend health
curl http://localhost:8000/
# Returns: {"status":"online"...}

# Stats endpoint
curl http://localhost:8000/stats
# Returns: {"total_incidents":150,...}
```

### Performance Monitoring
Add logging to track:
- Request count and latency
- BERT inference time
- Database query performance
- Error rates

---

## Scaling

| Daily Log Volume | Configuration | Hardware |
|-----------------|---------------|----------|
| < 10K | Single server, batch processing | 4 CPU, 8GB RAM |
| 10K - 100K | Single GPU server, 15-min batches | RTX 3050, 16GB RAM |
| 100K - 1M | GPU server, real-time streaming | RTX 3080, 32GB RAM |
| > 1M | Multi-GPU cluster with load balancer | A100 cluster |

---

## Common Issues

### Port already in use
```bash
# Find process using port
sudo lsof -i :8000
# or
sudo netstat -tlnp | grep 8000

# Kill process
kill -9 [PID]
```

### Permission denied (ports < 1024)
Use sudo or change to port > 1024 (e.g., 8080, 8000)

### Connection timeout from mobile
- Check firewall rules
- Verify router port forwarding
- Confirm backend is on `0.0.0.0`, not `127.0.0.1`
- Test from another device on same network first

---

## Quick Reference Commands

```bash
# Start backend (remote access)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend
cd frontend && python3 -m http.server 8080 --bind 0.0.0.0

# Check ports
netstat -tulnp | grep -E ':(8000|8080)'

# Test backend
curl http://localhost:8000/

# View logs
tail -f /var/log/soc-backend.log

# Restart services
sudo systemctl restart soc-backend
```

---

**Last Updated:** March 6, 2026  
**Version:** 1.0.0
