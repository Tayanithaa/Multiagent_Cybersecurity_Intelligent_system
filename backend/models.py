"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class LogEntry(BaseModel):
    """Single log entry for analysis"""
    timestamp: str
    user: Optional[str] = ""
    ip: Optional[str] = ""
    raw_message: str
    event_type: Optional[str] = ""
    status: Optional[str] = ""


class AnalyzeRequest(BaseModel):
    """Request model for log analysis"""
    logs: List[LogEntry]
    
    class Config:
        json_schema_extra = {
            "example": {
                "logs": [
                    {
                        "timestamp": "2026-01-03 10:00:00",
                        "user": "alice",
                        "ip": "192.168.1.100",
                        "raw_message": "Multiple failed login attempts detected",
                        "event_type": "auth",
                        "status": "failed"
                    }
                ]
            }
        }


class Incident(BaseModel):
    """Processed security incident"""
    id: Optional[int] = None
    timestamp: str
    user: Optional[str] = ""
    ip: Optional[str] = ""
    raw_message: str
    bert_class: str
    bert_confidence: float
    severity: str
    threat_type: str
    correlated_events: int
    ti_risk_score: float
    ti_indicators: List[str] = []
    recommended_action: str
    action_priority: int
    avg_confidence: float
    created_at: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-03 10:00:00",
                "user": "alice",
                "ip": "192.168.1.100",
                "raw_message": "Multiple failed login attempts",
                "bert_class": "brute_force",
                "bert_confidence": 0.95,
                "severity": "HIGH",
                "threat_type": "brute_force",
                "correlated_events": 3,
                "ti_risk_score": 0.85,
                "ti_indicators": ["known_attacker"],
                "recommended_action": "Block IP immediately",
                "action_priority": 1,
                "avg_confidence": 0.90
            }
        }


class AnalyzeResponse(BaseModel):
    """Response from analysis endpoint"""
    status: str
    incidents_detected: int
    incidents: List[Incident]
    message: str


class StatsResponse(BaseModel):
    """Dashboard statistics"""
    total_incidents: int
    high_severity: int
    medium_severity: int
    low_severity: int
    avg_confidence: float
    threat_types: dict
