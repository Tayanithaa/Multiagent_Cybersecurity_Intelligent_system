"""
Database module for storing and retrieving security incidents
Uses SQLite for simplicity (can be upgraded to PostgreSQL later)
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os


class IncidentDatabase:
    """SQLite database for storing security incidents"""
    
    def __init__(self, db_path="backend/incidents.db"):
        """Initialize database connection and create tables"""
        self.db_path = db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self._create_tables()
    
    def _create_tables(self):
        """Create incidents table if not exists"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT,
                ip TEXT,
                raw_message TEXT NOT NULL,
                bert_class TEXT,
                bert_confidence REAL,
                severity TEXT,
                threat_type TEXT,
                correlated_events INTEGER,
                ti_risk_score REAL,
                ti_indicators TEXT,
                recommended_action TEXT,
                action_priority INTEGER,
                avg_confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def insert_incident(self, incident: Dict) -> int:
        """
        Insert a single incident into database
        
        Args:
            incident: Dictionary with incident data
            
        Returns:
            ID of inserted incident
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO incidents (
                timestamp, user, ip, raw_message, bert_class, bert_confidence,
                severity, threat_type, correlated_events, ti_risk_score,
                ti_indicators, recommended_action, action_priority, avg_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident.get('timestamp', ''),
            incident.get('user', ''),
            incident.get('ip', ''),
            incident.get('raw_message', ''),
            incident.get('bert_class', ''),
            incident.get('bert_confidence', 0.0),
            incident.get('severity', 'LOW'),
            incident.get('threat_type', ''),
            incident.get('correlated_events', 0),
            incident.get('ti_risk_score', 0.0),
            json.dumps(incident.get('ti_indicators', [])),
            incident.get('recommended_action', ''),
            incident.get('action_priority', 3),
            incident.get('avg_confidence', 0.0)
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def insert_incidents_bulk(self, incidents: List[Dict]) -> int:
        """
        Insert multiple incidents at once
        
        Args:
            incidents: List of incident dictionaries
            
        Returns:
            Number of incidents inserted
        """
        cursor = self.conn.cursor()
        data = []
        for inc in incidents:
            data.append((
                inc.get('timestamp', ''),
                inc.get('user', ''),
                inc.get('ip', ''),
                inc.get('raw_message', ''),
                inc.get('bert_class', ''),
                inc.get('bert_confidence', 0.0),
                inc.get('severity', 'LOW'),
                inc.get('threat_type', ''),
                inc.get('correlated_events', 0),
                inc.get('ti_risk_score', 0.0),
                json.dumps(inc.get('ti_indicators', [])),
                inc.get('recommended_action', ''),
                inc.get('action_priority', 3),
                inc.get('avg_confidence', 0.0)
            ))
        
        cursor.executemany("""
            INSERT INTO incidents (
                timestamp, user, ip, raw_message, bert_class, bert_confidence,
                severity, threat_type, correlated_events, ti_risk_score,
                ti_indicators, recommended_action, action_priority, avg_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        self.conn.commit()
        return len(incidents)
    
    def get_all_incidents(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all incidents from database
        
        Args:
            limit: Maximum number of incidents to return (None = all)
            
        Returns:
            List of incident dictionaries
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM incidents ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        incidents = []
        for row in rows:
            inc = dict(row)
            # Parse JSON field
            if inc.get('ti_indicators'):
                try:
                    inc['ti_indicators'] = json.loads(inc['ti_indicators'])
                except:
                    inc['ti_indicators'] = []
            incidents.append(inc)
        
        return incidents
    
    def get_incident_by_id(self, incident_id: int) -> Optional[Dict]:
        """Get single incident by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        
        if row:
            inc = dict(row)
            if inc.get('ti_indicators'):
                try:
                    inc['ti_indicators'] = json.loads(inc['ti_indicators'])
                except:
                    inc['ti_indicators'] = []
            return inc
        return None
    
    def get_incidents_by_severity(self, severity: str) -> List[Dict]:
        """Get incidents filtered by severity level"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM incidents WHERE severity = ? ORDER BY created_at DESC",
            (severity,)
        )
        rows = cursor.fetchall()
        
        incidents = []
        for row in rows:
            inc = dict(row)
            if inc.get('ti_indicators'):
                try:
                    inc['ti_indicators'] = json.loads(inc['ti_indicators'])
                except:
                    inc['ti_indicators'] = []
            incidents.append(inc)
        
        return incidents
    
    def clear_all_incidents(self) -> int:
        """Delete all incidents (for testing)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM incidents")
        self.conn.commit()
        return cursor.rowcount
    
    def close(self):
        """Close database connection"""
        self.conn.close()


# Global database instance
_db_instance = None

def get_db() -> IncidentDatabase:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = IncidentDatabase()
    return _db_instance
