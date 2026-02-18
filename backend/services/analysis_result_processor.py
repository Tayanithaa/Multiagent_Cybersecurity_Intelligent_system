"""
Analysis Result Processor
Process sanitized malware analysis results from DMZ
Run BERT classification and update detection patterns
Machine 1 - Safe Zone
"""
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.bert_detection import BERTLogClassifier


class AnalysisResultProcessor:
    """
    Process sandbox analysis results with BERT models
    Extract threat intelligence and update detection patterns
    """
    
    def __init__(self, bert_model_path: str = "models/distilbert_log_classifier"):
        """
        Initialize result processor with BERT model
        
        Args:
            bert_model_path: Path to trained BERT model
        """
        try:
            self.bert_classifier = BERTLogClassifier(model_path=bert_model_path)
            self.bert_available = True
        except Exception as e:
            print(f"⚠️  BERT model not available: {e}")
            self.bert_available = False
    
    async def process_result(self, sanitized_result: Dict, db_connection) -> Dict:
        """
        Process sandbox analysis result and run BERT classification
        
        Args:
            sanitized_result: Sanitized analysis result from DMZ
            db_connection: Database connection
            
        Returns:
            Final analysis result with BERT classification
        """
        file_hash = sanitized_result['file_hash']
        
        # 1. Create behavioral description for BERT
        description = self._create_behavioral_description(sanitized_result)
        
        # 2. Run BERT threat classification (if available)
        if self.bert_available:
            bert_prediction = await self._bert_classify(description)
        else:
            # Fallback to rule-based classification
            bert_prediction = self._fallback_classify(sanitized_result)
        
        # 3. Calculate risk score
        risk_score = self._calculate_risk_score(sanitized_result, bert_prediction)
        
        # 4. Extract IOCs (Indicators of Compromise)
        iocs = self._extract_iocs(sanitized_result)
        
        # 5. Generate recommendations
        recommendations = self._generate_recommendations(risk_score, bert_prediction, iocs)
        
        # 6. Compile final result
        final_result = {
            'file_hash': file_hash,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'threat_category': bert_prediction['category'],
            'confidence': bert_prediction['confidence'],
            'risk_score': risk_score,
            'severity': self._map_severity(risk_score),
            'malware_family': bert_prediction.get('family', 'Unknown'),
            'attack_techniques': sanitized_result.get('ml_predictions', {}).get('attack_techniques', []),
            'iocs': iocs,
            'recommendations': recommendations,
            'behavioral_summary': description,
            'static_analysis': sanitized_result.get('static_analysis', {}),
            'behavioral_analysis': sanitized_result.get('behavioral_analysis', {}),
            'ml_predictions': sanitized_result.get('ml_predictions', {})
        }
        
        # 7. Store in database
        await self._store_analysis_result(final_result, db_connection)
        
        # 8. Update submission status
        await self._update_submission_status(file_hash, 'completed', db_connection)
        
        # 9. Learn new patterns (if high confidence)
        if bert_prediction['confidence'] > 0.90 and risk_score > 80:
            await self._learn_new_pattern(final_result, db_connection)
        
        return final_result
    
    def _create_behavioral_description(self, result: Dict) -> str:
        """
        Convert structured analysis data to natural language for BERT
        """
        static = result.get('static_analysis', {})
        behavioral = result.get('behavioral_analysis', {})
        ml_pred = result.get('ml_predictions', {})
        
        # Count operations
        network_count = len(behavioral.get('network_connections', []))
        files_created = len([f for f in behavioral.get('files_created', []) 
                            if f.get('operation') == 'create'])
        files_modified = len([f for f in behavioral.get('files_created', []) 
                             if f.get('operation') == 'modify'])
        registry_changes = len(behavioral.get('registry_modifications', []))
        
        # Get top IPs
        top_ips = [conn['ip'] for conn in behavioral.get('network_connections', [])[:5]]
        
        # Get attack techniques
        techniques = ml_pred.get('attack_techniques', [])
        
        description = f"""
Security Analysis Report

File Information:
- Type: {static.get('file_type', 'Unknown')}
- Size: {static.get('size', 0)} bytes
- Entropy: {static.get('entropy', 0):.2f}

Network Activity:
- Total unique connections: {network_count}
- Contacted IPs: {', '.join(top_ips) if top_ips else 'None'}

File System Operations:
- Files created: {files_created}
- Files modified: {files_modified}
- Total file operations: {files_created + files_modified}

Registry Modifications:
- Registry keys changed: {registry_changes}

Machine Learning Analysis:
- EMBER malware probability: {ml_pred.get('ember_score', 0):.2%}
- MalConv score: {ml_pred.get('malconv_score', 0):.2%}
- Detected MITRE ATT&CK techniques: {', '.join(techniques) if techniques else 'None'}
- C2 communication confidence: {ml_pred.get('c2_confidence', 0):.2%}

Behavioral Summary:
This sample exhibited {'suspicious' if ml_pred.get('ember_score', 0) > 0.5 else 'benign'} behavior patterns.
        """.strip()
        
        return description
    
    async def _bert_classify(self, description: str) -> Dict:
        """
        Run BERT classification on behavioral description
        """
        try:
            import pandas as pd
            
            # Create DataFrame with single row
            df = pd.DataFrame([{'raw_message': description}])
            
            # Run BERT detection
            result_df = self.bert_classifier.classify_batch(df)
            
            if len(result_df) > 0:
                row = result_df.iloc[0]
                return {
                    'category': row['bert_class'],
                    'confidence': row['bert_confidence'],
                    'family': row.get('bert_class', 'Unknown')
                }
            
        except Exception as e:
            print(f"Error in BERT classification: {e}")
        
        # Fallback
        return {
            'category': 'unknown',
            'confidence': 0.5,
            'family': 'Unknown'
        }
    
    def _fallback_classify(self, result: Dict) -> Dict:
        """
        Simple rule-based classification when BERT is not available
        """
        ml_pred = result.get('ml_predictions', {})
        ember_score = ml_pred.get('ember_score', 0)
        
        if ember_score > 0.8:
            category = 'malware'
            confidence = ember_score
        elif ember_score > 0.5:
            category = 'suspicious'
            confidence = ember_score
        else:
            category = 'normal'
            confidence = 1 - ember_score
        
        return {
            'category': category,
            'confidence': confidence,
            'family': 'Unknown'
        }
    
    def _calculate_risk_score(self, result: Dict, bert_prediction: Dict) -> int:
        """
        Calculate overall risk score (0-100)
        """
        ml_pred = result.get('ml_predictions', {})
        behavioral = result.get('behavioral_analysis', {})
        
        # Component scores
        ember_score = ml_pred.get('ember_score', 0) * 30  # Max 30 points
        bert_confidence = bert_prediction['confidence'] * 30  # Max 30 points
        
        # Network activity score
        network_count = len(behavioral.get('network_connections', []))
        network_score = min(network_count / 10 * 15, 15)  # Max 15 points
        
        # File operations score
        file_ops = len(behavioral.get('files_created', []))
        file_score = min(file_ops / 20 * 10, 10)  # Max 10 points
        
        # Attack techniques score
        technique_count = len(ml_pred.get('attack_techniques', []))
        technique_score = min(technique_count / 5 * 15, 15)  # Max 15 points
        
        total_score = ember_score + bert_confidence + network_score + file_score + technique_score
        
        return int(min(total_score, 100))
    
    def _map_severity(self, risk_score: int) -> str:
        """
        Map risk score to severity level
        """
        if risk_score >= 80:
            return 'CRITICAL'
        elif risk_score >= 60:
            return 'HIGH'
        elif risk_score >= 40:
            return 'MEDIUM'
        elif risk_score >= 20:
            return 'LOW'
        else:
            return 'INFO'
    
    def _extract_iocs(self, result: Dict) -> Dict[str, List]:
        """
        Extract Indicators of Compromise (IOCs)
        """
        behavioral = result.get('behavioral_analysis', {})
        
        iocs = {
            'ip_addresses': [],
            'domains': [],
            'file_paths': [],
            'registry_keys': [],
            'mutexes': []
        }
        
        # Extract IPs
        for conn in behavioral.get('network_connections', []):
            if 'ip' in conn:
                iocs['ip_addresses'].append({
                    'value': conn['ip'],
                    'port': conn.get('port'),
                    'country': conn.get('country', 'Unknown')
                })
        
        # Extract file paths
        for file_op in behavioral.get('files_created', []):
            if 'path' in file_op:
                iocs['file_paths'].append({
                    'value': file_op['path'],
                    'operation': file_op.get('operation')
                })
        
        # Extract registry keys
        for reg_op in behavioral.get('registry_modifications', []):
            if 'key' in reg_op:
                iocs['registry_keys'].append({
                    'value': reg_op['key'],
                    'operation': reg_op.get('operation')
                })
        
        return iocs
    
    def _generate_recommendations(self, risk_score: int, bert_prediction: Dict, 
                                  iocs: Dict) -> List[str]:
        """
        Generate security recommendations based on analysis
        """
        recommendations = []
        
        if risk_score >= 80:
            recommendations.append("CRITICAL: Isolate affected systems immediately")
            recommendations.append("Block all identified IP addresses at firewall level")
            recommendations.append("Conduct full forensic investigation")
        elif risk_score >= 60:
            recommendations.append("HIGH: Quarantine affected systems")
            recommendations.append("Monitor network traffic for identified IOCs")
        elif risk_score >= 40:
            recommendations.append("MEDIUM: Increase monitoring for similar patterns")
            recommendations.append("Review logs for related activity")
        else:
            recommendations.append("LOW: Continue standard monitoring")
        
        # IP-specific recommendations
        if len(iocs['ip_addresses']) > 0:
            recommendations.append(f"Block {len(iocs['ip_addresses'])} suspicious IP addresses")
        
        # File-specific recommendations
        if len(iocs['file_paths']) > 10:
            recommendations.append("High file system activity detected - review all file operations")
        
        return recommendations
    
    async def _store_analysis_result(self, result: Dict, db_connection):
        """
        Store final analysis result in database
        """
        try:
            import json
            
            query = """
                INSERT INTO malware_analysis 
                (file_hash, analysis_timestamp, threat_category, confidence, risk_score, 
                 severity, malware_family, attack_techniques, iocs, recommendations, 
                 behavioral_summary, full_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await db_connection.execute(
                query,
                (
                    result['file_hash'],
                    result['analysis_timestamp'],
                    result['threat_category'],
                    result['confidence'],
                    result['risk_score'],
                    result['severity'],
                    result['malware_family'],
                    json.dumps(result['attack_techniques']),
                    json.dumps(result['iocs']),
                    json.dumps(result['recommendations']),
                    result['behavioral_summary'],
                    json.dumps(result)
                )
            )
            
            print(f"✅ Analysis result stored for {result['file_hash']}")
            
        except Exception as e:
            print(f"Error storing analysis result: {e}")
            raise
    
    async def _update_submission_status(self, file_hash: str, status: str, db_connection):
        """
        Update submission status in database
        """
        try:
            query = """
                UPDATE malware_submissions 
                SET status = ?, completed_timestamp = ?
                WHERE file_hash = ?
            """
            
            await db_connection.execute(
                query,
                (status, datetime.utcnow().isoformat(), file_hash)
            )
            
        except Exception as e:
            print(f"Error updating submission status: {e}")
    
    async def _learn_new_pattern(self, result: Dict, db_connection):
        """
        Learn new threat pattern from high-confidence analysis
        Store for future model retraining
        """
        try:
            query = """
                INSERT INTO learned_patterns 
                (file_hash, threat_category, confidence, risk_score, 
                 pattern_signature, discovered_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            import json
            pattern_signature = json.dumps({
                'attack_techniques': result['attack_techniques'],
                'iocs': result['iocs'],
                'behavioral_summary': result['behavioral_summary']
            })
            
            await db_connection.execute(
                query,
                (
                    result['file_hash'],
                    result['threat_category'],
                    result['confidence'],
                    result['risk_score'],
                    pattern_signature,
                    datetime.utcnow().isoformat()
                )
            )
            
            print(f"🎓 New pattern learned: {result['threat_category']}")
            
        except Exception as e:
            print(f"Error learning new pattern: {e}")
