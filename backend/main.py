"""
FastAPI Backend Server for Multi-Agent SOC Dashboard
Integrates all agents: BERT Detection, Correlation, TI Enrichment, Response
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pandas as pd
import io
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db
from backend.models import (
    LogEntry, AnalyzeRequest, AnalyzeResponse, 
    Incident, StatsResponse
)
from agents.bert_detection import bert_detect
from agents.correlation import correlate_alerts
from agents.ti_enrichment import enrich_with_threat_intel
from agents.response_agent import recommend_response

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent SOC API",
    description="Backend API for AI-powered Security Operations Center",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database instance
db = get_db()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Multi-Agent SOC API",
        "version": "1.0.0",
        "agents": ["BERT Detection", "Correlation", "TI Enrichment", "Response"]
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check database
        incidents = db.get_all_incidents(limit=1)
        return {
            "status": "healthy",
            "database": "connected",
            "total_incidents": len(db.get_all_incidents())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_logs(request: AnalyzeRequest):
    """
    Analyze logs through the complete agent pipeline:
    1. BERT Detection → classify threats
    2. Correlation → find related events
    3. TI Enrichment → add threat intelligence
    4. Response → generate recommended actions
    """
    try:
        # Convert request to DataFrame
        logs_data = [log.model_dump() for log in request.logs]
        df = pd.DataFrame(logs_data)
        
        if df.empty:
            return AnalyzeResponse(
                status="success",
                incidents_detected=0,
                incidents=[],
                message="No logs provided"
            )
        
        # Ensure required columns exist
        if 'raw_message' not in df.columns and 'message' not in df.columns:
            raise HTTPException(
                status_code=400, 
                detail="Logs must contain 'raw_message' or 'message' field"
            )
        
        # Pipeline: Step 1 - BERT Detection
        print("🔍 Running BERT detection...")
        df = bert_detect(df)
        
        # Filter only anomalies for further processing
        threats_df = df[df['bert_class'] != 'normal'].copy()
        
        if len(threats_df) == 0:
            return AnalyzeResponse(
                status="success",
                incidents_detected=0,
                incidents=[],
                message=f"Analyzed {len(df)} logs, no threats detected"
            )
        
        # Add missing columns for database compatibility
        if 'threat_type' not in threats_df.columns:
            threats_df['threat_type'] = threats_df['bert_class']
        if 'correlated_events' not in threats_df.columns:
            threats_df['correlated_events'] = 1
        if 'ti_risk_score' not in threats_df.columns:
            threats_df['ti_risk_score'] = threats_df['bert_confidence']
        if 'ti_indicators' not in threats_df.columns:
            threats_df['ti_indicators'] = threats_df['bert_class'].apply(lambda x: [x])
        if 'recommended_action' not in threats_df.columns:
            threats_df['recommended_action'] = threats_df.apply(
                lambda row: f"Investigate {row['bert_class']} from {row.get('ip', row.get('source_ip', 'unknown'))}", 
                axis=1
            )
        if 'action_priority' not in threats_df.columns:
            threats_df['action_priority'] = threats_df['severity'].map({'HIGH': 1, 'MEDIUM': 2, 'LOW': 3})
        if 'avg_confidence' not in threats_df.columns:
            threats_df['avg_confidence'] = threats_df['bert_confidence']
        
        # Save to database
        incidents_list = threats_df.to_dict('records')
        if incidents_list:
            db.insert_incidents_bulk(incidents_list)
        
        # Convert to Pydantic models
        incidents = [Incident(**inc) for inc in incidents_list]
        
        return AnalyzeResponse(
            status="success",
            incidents_detected=len(incidents),
            incidents=incidents,
            message=f"Analyzed {len(df)} logs, detected {len(incidents)} incidents"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload and analyze CSV file of logs
    Expected CSV format: timestamp,user,ip,raw_message
    """
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        print(f"📁 Uploaded CSV columns: {df.columns.tolist()}")
        print(f"📁 Rows: {len(df)}")
        
        # Validate columns
        if not any(col in df.columns for col in ['raw_message', 'message']):
            raise HTTPException(
                status_code=400,
                detail=f"CSV must contain 'raw_message' or 'message' column. Found: {df.columns.tolist()}"
            )
        
        # Fill missing columns with defaults
        if 'timestamp' not in df.columns:
            df['timestamp'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'user' not in df.columns:
            df['user'] = 'unknown'
        if 'ip' not in df.columns and 'source_ip' not in df.columns:
            df['ip'] = 'unknown'
        
        # Run BERT detection
        print(f"🔍 Running BERT detection...")
        df = bert_detect(df)
        print(f"✅ BERT detection complete")
        
        # Extract threats and prepare for database
        incidents_df = df[df['bert_class'] != 'normal'].copy()
        print(f"📊 Found {len(incidents_df)} incidents (non-normal)")
        
        # Add missing columns
        if 'threat_type' not in incidents_df.columns:
            incidents_df['threat_type'] = incidents_df['bert_class']
        if 'correlated_events' not in incidents_df.columns:
            incidents_df['correlated_events'] = 1
        if 'ti_risk_score' not in incidents_df.columns:
            incidents_df['ti_risk_score'] = incidents_df['bert_confidence']
        if 'ti_indicators' not in incidents_df.columns:
            incidents_df['ti_indicators'] = incidents_df['bert_class'].apply(lambda x: [x])
        if 'recommended_action' not in incidents_df.columns:
            incidents_df['recommended_action'] = incidents_df.apply(
                lambda row: f"Investigate {row['bert_class']} from {row.get('ip', row.get('source_ip', 'unknown'))}", 
                axis=1
            )
        if 'action_priority' not in incidents_df.columns:
            incidents_df['action_priority'] = incidents_df['severity'].map({'HIGH': 1, 'MEDIUM': 2, 'LOW': 3})
        if 'avg_confidence' not in incidents_df.columns:
            incidents_df['avg_confidence'] = incidents_df['bert_confidence']
        
        incidents_list = incidents_df.to_dict('records')
        
        if incidents_list:
            print(f"💾 Saving {len(incidents_list)} incidents to database...")
            db.insert_incidents_bulk(incidents_list)
            print(f"✅ Saved to database")
        
        return {
            "status": "success",
            "filename": file.filename,
            "total_logs": len(df),
            "incidents_detected": len(incidents_list),
            "incidents": incidents_list,
            "message": f"Processed {len(df)} logs from {file.filename}"
        }
        
    except pd.errors.ParserError as e:
        print(f"❌ CSV parsing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/connect/test")
async def test_connection(payload: dict):
    """
    Test connectivity to a remote URL (log API or model endpoint).
    Returns status, latency, and a row count estimate if the response is JSON.
    """
    import time, requests as req
    url = payload.get("url", "").strip()
    token = payload.get("token", "").strip()

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    headers = {}
    if token:
        headers["Authorization"] = token if token.startswith("Bearer ") else f"Bearer {token}"

    try:
        start = time.time()
        r = req.get(url, headers=headers, timeout=10)
        latency_ms = int((time.time() - start) * 1000)
        r.raise_for_status()

        # Try to count rows in JSON response
        rows_available = None
        try:
            data = r.json()
            if isinstance(data, list):
                rows_available = len(data)
            elif isinstance(data, dict):
                for key in ("data", "logs", "records", "events", "results"):
                    if key in data and isinstance(data[key], list):
                        rows_available = len(data[key])
                        break
        except Exception:
            pass

        return {
            "status": "ok",
            "http_status": r.status_code,
            "latency_ms": latency_ms,
            "rows_available": rows_available,
            "message": f"Connection successful ({latency_ms}ms)"
        }

    except req.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Could not connect to the URL. Check the address.")
    except req.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Connection timed out after 10s.")
    except req.exceptions.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Remote returned HTTP {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@app.post("/fetch-remote")
async def fetch_remote_logs(payload: dict):
    """
    Fetch logs from a remote REST API URL, run the full BERT pipeline, and return incidents.
    The remote URL must return JSON: either a list of log objects, or a dict with a list under
    a common key (data / logs / records / events / results).
    """
    import requests as req

    url = payload.get("url", "").strip()
    token = payload.get("token", "").strip()
    limit = int(payload.get("limit", 500))
    api_key = payload.get("api_key", "").strip()  # reserved for future cloud model auth

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = token if token.startswith("Bearer ") else f"Bearer {token}"
    if api_key:
        headers["X-API-Key"] = api_key

    # Fetch logs
    try:
        r = req.get(url, headers=headers, params={"limit": limit}, timeout=30)
        r.raise_for_status()
        raw = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch from remote URL: {str(e)}")

    # Normalize to list
    if isinstance(raw, list):
        records = raw[:limit]
    elif isinstance(raw, dict):
        records = None
        for key in ("data", "logs", "records", "events", "results"):
            if key in raw and isinstance(raw[key], list):
                records = raw[key][:limit]
                break
        if records is None:
            raise HTTPException(status_code=422, detail="Remote JSON must be a list or have a 'data'/'logs'/'records' key containing a list.")
    else:
        raise HTTPException(status_code=422, detail="Unexpected JSON format from remote URL.")

    if not records:
        return {"status": "success", "total_logs": 0, "incidents_detected": 0, "incidents": [], "message": "No log records returned from remote URL."}

    # Build DataFrame — normalize common field names
    df = pd.DataFrame(records)
    print(f"📡 Remote fetch: {len(df)} rows, columns: {df.columns.tolist()}")

    # Map common field names → expected names
    rename_map = {
        "message": "raw_message", "log_message": "raw_message", "msg": "raw_message",
        "source_ip": "ip", "src_ip": "ip", "attacker_ip": "ip",
        "created_at": "timestamp", "time": "timestamp", "event_time": "timestamp",
        "username": "user", "actor": "user",
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    if "raw_message" not in df.columns and "message" not in df.columns:
        raise HTTPException(status_code=422, detail=f"Remote records must contain a message/raw_message field. Got: {df.columns.tolist()}")

    if "timestamp" not in df.columns:
        df["timestamp"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    if "user" not in df.columns:
        df["user"] = "unknown"
    if "ip" not in df.columns:
        df["ip"] = "unknown"

    # Run BERT pipeline
    print("🔍 Running BERT detection on remote logs...")
    df = bert_detect(df)
    incidents_df = df[df["bert_class"] != "normal"].copy()
    print(f"📊 Found {len(incidents_df)} incidents from remote source")

    # Fill required columns
    for col, fn in [
        ("threat_type", lambda r: r["bert_class"]),
        ("correlated_events", lambda r: 1),
        ("ti_risk_score", lambda r: r["bert_confidence"]),
        ("ti_indicators", lambda r: [r["bert_class"]]),
        ("recommended_action", lambda r: f"Investigate {r['bert_class']} from {r.get('ip', 'unknown')}"),
        ("action_priority", lambda r: {"HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(r["severity"], 3)),
        ("avg_confidence", lambda r: r["bert_confidence"]),
    ]:
        if col not in incidents_df.columns:
            incidents_df[col] = incidents_df.apply(fn, axis=1)

    incidents_list = incidents_df.to_dict("records")
    if incidents_list:
        db.insert_incidents_bulk(incidents_list)

    return {
        "status": "success",
        "source_url": url,
        "total_logs": len(df),
        "incidents_detected": len(incidents_list),
        "incidents": incidents_list,
        "message": f"Fetched {len(df)} logs from remote, detected {len(incidents_list)} incidents"
    }


@app.get("/incidents", response_model=List[Incident])
async def get_incidents(limit: int = None, severity: str = None):
    """
    Get all incidents from database
    Optional filters: limit, severity (HIGH/MEDIUM/LOW)
    """
    try:
        if severity:
            incidents_list = db.get_incidents_by_severity(severity.upper())
        else:
            incidents_list = db.get_all_incidents(limit=limit)
        
        return [Incident(**inc) for inc in incidents_list]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch incidents: {str(e)}")


@app.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: int):
    """Get single incident by ID"""
    try:
        incident = db.get_incident_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        return Incident(**incident)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch incident: {str(e)}")


@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Get dashboard statistics"""
    try:
        incidents = db.get_all_incidents()
        
        if not incidents:
            return StatsResponse(
                total_incidents=0,
                high_severity=0,
                medium_severity=0,
                low_severity=0,
                avg_confidence=0.0,
                threat_types={}
            )
        
        # Calculate stats
        high = sum(1 for inc in incidents if inc['severity'] == 'HIGH')
        medium = sum(1 for inc in incidents if inc['severity'] == 'MEDIUM')
        low = sum(1 for inc in incidents if inc['severity'] == 'LOW')
        
        avg_conf = sum(inc['avg_confidence'] for inc in incidents) / len(incidents)
        
        # Threat type distribution
        threat_types = {}
        for inc in incidents:
            threat = inc['threat_type']
            threat_types[threat] = threat_types.get(threat, 0) + 1
        
        return StatsResponse(
            total_incidents=len(incidents),
            high_severity=high,
            medium_severity=medium,
            low_severity=low,
            avg_confidence=avg_conf,
            threat_types=threat_types
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@app.delete("/incidents")
async def clear_incidents():
    """Clear all incidents (for testing/demo)"""
    try:
        count = db.clear_all_incidents()
        return {
            "status": "success",
            "deleted": count,
            "message": f"Cleared {count} incidents"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear incidents: {str(e)}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("="*80)
    print("🚀 Multi-Agent SOC API Starting...")
    print("="*80)
    print("📊 Dashboard: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔍 Agents: BERT Detection → Correlation → TI Enrichment → Response")
    print("="*80)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
