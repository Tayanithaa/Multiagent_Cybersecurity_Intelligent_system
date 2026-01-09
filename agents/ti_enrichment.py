"""
THREAT INTELLIGENCE ENRICHMENT AGENT
Adds context and explanations to detected threats using static threat intel database
"""
import pandas as pd


# Static Threat Intelligence Database
THREAT_INTEL_DB = {
    'brute_force': {
        'category': 'Authentication Attack',
        'description': 'Multiple failed login attempts indicating password guessing or credential stuffing',
        'indicators': ['Failed authentication', 'Invalid credentials', 'Account lockout'],
        'risk_level': 'MEDIUM',
        'typical_impact': 'Account compromise, unauthorized access',
        'mitigation': 'Implement account lockout policies, enable MFA, monitor failed login patterns'
    },
    'malware': {
        'category': 'Malicious Software',
        'description': 'Detected malware activity including trojans, viruses, or malicious code execution',
        'indicators': ['Malware signature match', 'Suspicious process execution', 'File hash match'],
        'risk_level': 'HIGH',
        'typical_impact': 'System compromise, data theft, ransomware deployment',
        'mitigation': 'Isolate affected systems, run full antivirus scan, analyze malware sample'
    },
    'phishing': {
        'category': 'Social Engineering',
        'description': 'Phishing attempt detected - fraudulent communication to steal credentials or data',
        'indicators': ['Suspicious email links', 'Credential harvesting page', 'Domain spoofing'],
        'risk_level': 'MEDIUM',
        'typical_impact': 'Credential theft, business email compromise, financial fraud',
        'mitigation': 'Block malicious URLs, user security awareness training, email filtering'
    },
    'ddos': {
        'category': 'Denial of Service',
        'description': 'Distributed denial of service attack - flood of traffic to overwhelm services',
        'indicators': ['Abnormal traffic volume', 'Service degradation', 'Multiple source IPs'],
        'risk_level': 'MEDIUM',
        'typical_impact': 'Service unavailability, business disruption, revenue loss',
        'mitigation': 'Enable DDoS protection, rate limiting, traffic filtering, CDN deployment'
    },
    'ransomware': {
        'category': 'Extortion Malware',
        'description': 'Ransomware detected - malware that encrypts files and demands payment',
        'indicators': ['File encryption activity', 'Ransom note detected', 'Mass file modification'],
        'risk_level': 'HIGH',
        'typical_impact': 'Data encryption, business operations halt, financial extortion',
        'mitigation': 'IMMEDIATE ISOLATION, restore from backups, do not pay ransom, contact authorities'
    },
    'data_exfil': {
        'category': 'Data Breach',
        'description': 'Unauthorized data exfiltration - sensitive data being transmitted to external location',
        'indicators': ['Large data transfers', 'Unusual network traffic', 'External connections'],
        'risk_level': 'HIGH',
        'typical_impact': 'Data breach, intellectual property theft, regulatory violations',
        'mitigation': 'Block external connections, review DLP policies, investigate data access logs'
    },
    'insider_threat': {
        'category': 'Insider Activity',
        'description': 'Suspicious insider activity - authorized user acting maliciously or negligently',
        'indicators': ['Privilege escalation', 'After-hours access', 'Data hoarding'],
        'risk_level': 'HIGH',
        'typical_impact': 'Data theft, sabotage, privilege abuse, competitive intelligence loss',
        'mitigation': 'Review user permissions, investigate user activity, disable account if needed'
    },
    'normal': {
        'category': 'Normal Activity',
        'description': 'Standard system or user activity with no security concerns',
        'indicators': ['Normal login', 'Standard operations', 'Expected behavior'],
        'risk_level': 'LOW',
        'typical_impact': 'None',
        'mitigation': 'No action required - continue monitoring'
    }
}


def enrich_with_threat_intel(incidents_df):
    """
    Enrich incident data with threat intelligence context
    
    Args:
        incidents_df: DataFrame from correlation agent with columns:
                     [source_ip, time_window, threat_type, alert_count, avg_confidence, severity, users]
    
    Returns:
        DataFrame with added TI columns:
        - ti_category: Threat category
        - ti_description: Detailed explanation
        - ti_risk_level: Risk assessment
        - ti_impact: Potential business impact
        - ti_mitigation: Recommended actions
    """
    if incidents_df is None or len(incidents_df) == 0:
        print("⚠️  No incidents to enrich")
        return pd.DataFrame()
    
    enriched = incidents_df.copy()
    
    # Add threat intelligence fields
    enriched['ti_category'] = enriched['threat_type'].apply(
        lambda x: THREAT_INTEL_DB.get(x, {}).get('category', 'Unknown')
    )
    
    enriched['ti_description'] = enriched['threat_type'].apply(
        lambda x: THREAT_INTEL_DB.get(x, {}).get('description', 'No description available')
    )
    
    enriched['ti_risk_level'] = enriched['threat_type'].apply(
        lambda x: THREAT_INTEL_DB.get(x, {}).get('risk_level', 'UNKNOWN')
    )
    
    enriched['ti_impact'] = enriched['threat_type'].apply(
        lambda x: THREAT_INTEL_DB.get(x, {}).get('typical_impact', 'Unknown impact')
    )
    
    enriched['ti_mitigation'] = enriched['threat_type'].apply(
        lambda x: THREAT_INTEL_DB.get(x, {}).get('mitigation', 'Investigate further')
    )
    
    return enriched


def get_threat_details(threat_type):
    """
    Get detailed threat intelligence for a specific threat type
    
    Args:
        threat_type: String threat type (e.g., 'brute_force', 'malware')
    
    Returns:
        Dictionary with threat intelligence details
    """
    return THREAT_INTEL_DB.get(threat_type, {
        'category': 'Unknown',
        'description': 'No threat intelligence available',
        'indicators': [],
        'risk_level': 'UNKNOWN',
        'typical_impact': 'Unknown',
        'mitigation': 'Manual investigation required'
    })


def print_enriched_report(enriched_df):
    """
    Print a human-readable threat intelligence enriched report
    
    Args:
        enriched_df: DataFrame from enrich_with_threat_intel()
    """
    if len(enriched_df) == 0:
        print("\n📊 No enriched incidents to display")
        return
    
    print("\n" + "="*100)
    print("🔍 THREAT INTELLIGENCE ENRICHED INCIDENT REPORT")
    print("="*100)
    
    for idx, incident in enriched_df.iterrows():
        print(f"\n{'─'*100}")
        print(f"🚨 INCIDENT #{idx + 1}")
        print(f"{'─'*100}")
        print(f"Source IP:        {incident['source_ip']}")
        print(f"Time Window:      {incident['time_window']}")
        print(f"Threat Type:      {incident['threat_type'].upper()}")
        print(f"Alert Count:      {incident['alert_count']}")
        print(f"Avg Confidence:   {incident['avg_confidence']:.1%}")
        print(f"Severity:         {incident['severity']}")
        print(f"Users Affected:   {', '.join(incident['users']) if isinstance(incident['users'], list) else incident['users']}")
        
        print(f"\n📋 THREAT INTELLIGENCE:")
        print(f"  Category:       {incident['ti_category']}")
        print(f"  Risk Level:     {incident['ti_risk_level']}")
        print(f"  Description:    {incident['ti_description']}")
        print(f"  Potential Impact: {incident['ti_impact']}")
        print(f"  Mitigation:     {incident['ti_mitigation']}")
    
    print(f"\n{'='*100}")
    print(f"Total enriched incidents: {len(enriched_df)}")
    print(f"{'='*100}\n")


# Example usage for testing
if __name__ == "__main__":
    # Sample incidents data (would come from correlation agent)
    sample_incidents = pd.DataFrame({
        'source_ip': ['192.168.1.100', '10.0.0.50', '172.16.0.200'],
        'time_window': ['2026-01-05 10:00:00', '2026-01-05 10:05:00', '2026-01-05 10:10:00'],
        'threat_type': ['brute_force', 'malware', 'ransomware'],
        'alert_count': [25, 5, 3],
        'avg_confidence': [0.998, 0.995, 0.999],
        'severity': ['MEDIUM', 'HIGH', 'HIGH'],
        'users': [['admin', 'root'], ['john'], ['backup_service']]
    })
    
    print("\n🧪 Testing Threat Intelligence Enrichment")
    print("="*100)
    
    # Enrich incidents
    enriched = enrich_with_threat_intel(sample_incidents)
    
    # Print report
    print_enriched_report(enriched)
    
    # Test individual threat lookup
    print("\n🔍 Individual Threat Lookup Test:")
    threat_details = get_threat_details('malware')
    print(f"Threat: malware")
    print(f"Details: {threat_details}")
