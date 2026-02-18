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

# Import sandbox services
from backend.services.malware_submission_handler import MalwareSubmissionHandler
from backend.services.analysis_result_processor import AnalysisResultProcessor

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

# Initialize sandbox services
submission_handler = MalwareSubmissionHandler(quarantine_dir="quarantine")
result_processor = AnalysisResultProcessor()


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
  ============================================================================
# SANDBOX MALWARE ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/sandbox/submit")
async def submit_malware_sample(file: UploadFile = File(...), user_id: str = "demo_user"):
    """
    Submit malware sample for sandbox analysis
    
    **Security Note:** File is stored in quarantine with read-only permissions.
    No execution happens on this machine. Analysis is performed on isolated server.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Handle submission
        result = await submission_handler.handle_upload(
            file_content=file_content,
            filename=file.filename,
            user_id=user_id,
            db_connection=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")


@app.get("/api/sandbox/status/{task_id}")
async def get_sandbox_status(task_id: str):
    """
    Get status of submitted malware sample
    
    Args:
        task_id: File hash (returned from submit endpoint)
    """
    try:
        status = await submission_handler.get_submission_status(task_id, db)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.get("/api/sandbox/results/{task_id}")
async def get_analysis_results(task_id: str):
    """
    Get complete analysis results for a malware sample
    
    Args:
        task_id: File hash
    """
    try:
        # Query database for analysis result
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM malware_analysis 
            WHERE file_hash = ? 
            ORDER BY analysis_timestamp DESC 
            LIMIT 1
        """, (task_id,))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"No analysis found for {task_id}")
        
        # Convert to dictionary
        result_dict = dict(result)
        
        # Parse JSON fields
        import json
        if 'attack_techniques' in result_dict and result_dict['attack_techniques']:
            result_dict['attack_techniques'] = json.loads(result_dict['attack_techniques'])
        if 'iocs' in result_dict and result_dict['iocs']:
            result_dict['iocs'] = json.loads(result_dict['iocs'])
        if 'recommendations' in result_dict and result_dict['recommendations']:
            result_dict['recommendations'] = json.loads(result_dict['recommendations'])
        if 'full_result' in result_dict and result_dict['full_result']:
            result_dict['full_result'] = json.loads(result_dict['full_result'])
        
        return result_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@app.get("/api/sandbox/list")
async def list_submissions(limit: int = 50, status: str = None):
    """
    List recent malware submissions
    
    Args:
        limit: Maximum number of results
        status: Filter by status (queued, processing, completed, failed)
    """
    try:
        cursor = db.conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM malware_submissions 
                WHERE status = ?
                ORDER BY upload_timestamp DESC 
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT * FROM malware_submissions 
                ORDER BY upload_timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        results = cursor.fetchall()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list submissions: {str(e)}")


@app.post("/api/sandbox/process_result")
async def process_analysis_result(result: dict):
    """
    Process analysis result from DMZ orchestrator
    This endpoint is called by the DMZ server with sanitized results
    
    **Security:** Should be restricted to DMZ server IP in production
    """
    try:
        # Process result with BERT and store
        final_result = await result_processor.process_result(result, db)
        
        return {
            "status": "processed",
            "file_hash": final_result['file_hash'],
            "threat_category": final_result['threat_category'],
            "risk_score": final_result['risk_score']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/api/sandbox/stats")
async def get_sandbox_statistics():
    """
    Get sandbox analysis statistics
    """
    try:
        cursor = db.conn.cursor()
        
        # Total submissions
        cursor.execute("SELECT COUNT(*) as count FROM malware_submissions")
        total_submissions = cursor.fetchone()['count']
        
        # Completed analyses
        cursor.execute("SELECT COUNT(*) as count FROM malware_analysis")
        completed_analyses = cursor.fetchone()['count']
        
        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM malware_submissions 
            GROUP BY status
        """)
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # By threat category
        cursor.execute("""
            SELECT threat_category, COUNT(*) as count 
            FROM malware_analysis 
            GROUP BY threat_category
        """)
        threat_counts = {row['threat_category']: row['count'] for row in cursor.fetchall()}
        
        # Average risk score
        cursor.execute("SELECT AVG(risk_score) as avg_risk FROM malware_analysis")
        avg_risk = cursor.fetchone()['avg_risk'] or 0
        
        return {
            "total_submissions": total_submissions,
            "completed_analyses": completed_analyses,
            "status_breakdown": status_counts,
            "threat_categories": threat_counts,
            "average_risk_score": round(avg_risk, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


#   except Exception as e:
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
