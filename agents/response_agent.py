"""
RESPONSE RECOMMENDATION AGENT
Rule-based decision engine that recommends concrete security actions
"""
import pandas as pd


# Response action definitions
ACTIONS = {
    'BLOCK_IP': {
        'priority': 1,
        'description': 'Block source IP address at firewall',
        'automation': 'Can be automated',
        'tools': 'Firewall, IPS, WAF'
    },
    'ISOLATE_HOST': {
        'priority': 1,
        'description': 'Quarantine infected host from network',
        'automation': 'Can be automated',
        'tools': 'NAC, EDR, Network segmentation'
    },
    'ESCALATE': {
        'priority': 2,
        'description': 'Escalate to senior SOC analyst or incident response team',
        'automation': 'Semi-automated (alert)',
        'tools': 'SOAR, Ticketing system, PagerDuty'
    },
    'RESET_PASSWORD': {
        'priority': 2,
        'description': 'Force password reset for affected accounts',
        'automation': 'Can be automated',
        'tools': 'Active Directory, IAM'
    },
    'DISABLE_ACCOUNT': {
        'priority': 1,
        'description': 'Disable compromised user accounts',
        'automation': 'Can be automated',
        'tools': 'Active Directory, IAM'
    },
    'MONITOR': {
        'priority': 3,
        'description': 'Continue monitoring - no immediate action required',
        'automation': 'Automated',
        'tools': 'SIEM, Log monitoring'
    },
    'SCAN_SYSTEM': {
        'priority': 2,
        'description': 'Run full antivirus/EDR scan on affected systems',
        'automation': 'Can be automated',
        'tools': 'Antivirus, EDR platform'
    },
    'BLOCK_URL': {
        'priority': 2,
        'description': 'Block malicious URLs/domains',
        'automation': 'Can be automated',
        'tools': 'Web proxy, DNS filtering'
    },
    'RESTORE_BACKUP': {
        'priority': 1,
        'description': 'Restore systems from clean backup',
        'automation': 'Manual',
        'tools': 'Backup system, Recovery tools'
    },
    'NOTIFY_LEGAL': {
        'priority': 1,
        'description': 'Notify legal/compliance team for data breach',
        'automation': 'Manual',
        'tools': 'Email, Incident management'
    }
}


def recommend_response(enriched_df):
    """
    Recommend security response actions based on threat intelligence and severity
    
    Decision logic:
    - Severity HIGH + confidence >95% → Aggressive actions (BLOCK_IP, ISOLATE_HOST)
    - Severity HIGH + confidence <95% → Cautious actions (ESCALATE, MONITOR)
    - Severity MEDIUM → Moderate actions (RESET_PASSWORD, BLOCK_URL)
    - Multiple alerts (>10) → Automatic escalation
    - Specific threat types → Specialized actions
    
    Args:
        enriched_df: DataFrame from ti_enrichment agent with TI data
    
    Returns:
        DataFrame with added columns:
        - primary_action: Main recommended action
        - secondary_action: Backup/additional action
        - action_priority: Priority level (1=Critical, 2=High, 3=Medium)
        - automation_status: Whether action can be automated
    """
    if enriched_df is None or len(enriched_df) == 0:
        print("⚠️  No incidents to process")
        return pd.DataFrame()
    
    response_df = enriched_df.copy()
    
    # Apply decision rules
    response_df['primary_action'] = response_df.apply(_determine_primary_action, axis=1)
    response_df['secondary_action'] = response_df.apply(_determine_secondary_action, axis=1)
    
    # Add action metadata
    response_df['action_priority'] = response_df['primary_action'].apply(
        lambda x: ACTIONS.get(x, {}).get('priority', 3)
    )
    
    response_df['automation_status'] = response_df['primary_action'].apply(
        lambda x: ACTIONS.get(x, {}).get('automation', 'Unknown')
    )
    
    response_df['action_description'] = response_df['primary_action'].apply(
        lambda x: ACTIONS.get(x, {}).get('description', 'No description')
    )
    
    # Sort by priority (critical first)
    response_df = response_df.sort_values('action_priority')
    
    return response_df


def _determine_primary_action(row):
    """
    Internal function to determine primary action based on incident characteristics
    
    Decision tree:
    1. Check threat type (specific threats get specific actions)
    2. Check severity + confidence
    3. Check alert count (volume-based escalation)
    """
    threat = row['threat_type']
    severity = row['severity']
    confidence = row['avg_confidence']
    alert_count = row['alert_count']
    
    # Threat-specific actions (highest priority)
    if threat == 'ransomware':
        return 'ISOLATE_HOST'  # Critical - prevent spread
    
    elif threat == 'malware':
        if confidence >= 0.95:
            return 'ISOLATE_HOST'
        else:
            return 'SCAN_SYSTEM'
    
    elif threat == 'brute_force':
        if alert_count >= 20:
            return 'BLOCK_IP'  # Aggressive attack
        elif alert_count >= 10:
            return 'RESET_PASSWORD'  # Possible compromise
        else:
            return 'MONITOR'  # Low volume
    
    elif threat == 'phishing':
        return 'BLOCK_URL'
    
    elif threat == 'data_exfil':
        return 'BLOCK_IP'  # Stop data leak immediately
    
    elif threat == 'insider_threat':
        if confidence >= 0.95:
            return 'DISABLE_ACCOUNT'
        else:
            return 'ESCALATE'  # Needs human judgment
    
    elif threat == 'ddos':
        return 'BLOCK_IP'
    
    # Severity-based fallback rules
    elif severity == 'HIGH':
        if confidence >= 0.95:
            return 'BLOCK_IP'
        else:
            return 'ESCALATE'
    
    elif severity == 'MEDIUM':
        if alert_count >= 15:
            return 'ESCALATE'
        else:
            return 'MONITOR'
    
    else:  # LOW severity
        return 'MONITOR'


def _determine_secondary_action(row):
    """
    Determine secondary/backup action to take alongside primary action
    """
    threat = row['threat_type']
    primary = row['primary_action']
    
    # Ransomware always escalates + notifies
    if threat == 'ransomware':
        return 'NOTIFY_LEGAL' if primary != 'NOTIFY_LEGAL' else 'RESTORE_BACKUP'
    
    # Data exfil needs escalation
    elif threat == 'data_exfil':
        return 'ESCALATE' if primary != 'ESCALATE' else 'NOTIFY_LEGAL'
    
    # Malware needs scanning
    elif threat == 'malware':
        return 'SCAN_SYSTEM' if primary != 'SCAN_SYSTEM' else 'ESCALATE'
    
    # Brute force needs password reset
    elif threat == 'brute_force' and row['alert_count'] >= 10:
        return 'RESET_PASSWORD' if primary != 'RESET_PASSWORD' else 'MONITOR'
    
    # Insider threats always escalate
    elif threat == 'insider_threat':
        return 'ESCALATE'
    
    # Default: escalate high severity, monitor others
    elif row['severity'] == 'HIGH':
        return 'ESCALATE' if primary != 'ESCALATE' else 'MONITOR'
    else:
        return 'MONITOR'


def get_action_details(action_name):
    """
    Get detailed information about a specific action
    
    Args:
        action_name: String action name (e.g., 'BLOCK_IP')
    
    Returns:
        Dictionary with action details
    """
    return ACTIONS.get(action_name, {
        'priority': 3,
        'description': 'Unknown action',
        'automation': 'Unknown',
        'tools': 'Unknown'
    })


def print_response_report(response_df):
    """
    Print a human-readable response recommendation report
    
    Args:
        response_df: DataFrame from recommend_response()
    """
    if len(response_df) == 0:
        print("\n📊 No response recommendations to display")
        return
    
    print("\n" + "="*100)
    print("⚡ SECURITY RESPONSE RECOMMENDATIONS")
    print("="*100)
    
    # Summary statistics
    critical_count = len(response_df[response_df['action_priority'] == 1])
    high_count = len(response_df[response_df['action_priority'] == 2])
    medium_count = len(response_df[response_df['action_priority'] == 3])
    
    print(f"\n📈 SUMMARY:")
    print(f"  Total incidents: {len(response_df)}")
    print(f"  🔴 Critical actions (Priority 1): {critical_count}")
    print(f"  🟠 High actions (Priority 2):     {high_count}")
    print(f"  🟡 Medium actions (Priority 3):   {medium_count}")
    
    # Detailed incidents
    for idx, incident in response_df.iterrows():
        priority_emoji = '🔴' if incident['action_priority'] == 1 else '🟠' if incident['action_priority'] == 2 else '🟡'
        
        print(f"\n{'─'*100}")
        print(f"{priority_emoji} INCIDENT #{idx + 1} - PRIORITY {incident['action_priority']}")
        print(f"{'─'*100}")
        print(f"Source IP:          {incident['source_ip']}")
        print(f"Threat Type:        {incident['threat_type'].upper()}")
        print(f"Severity:           {incident['severity']}")
        print(f"Confidence:         {incident['avg_confidence']:.1%}")
        print(f"Alert Count:        {incident['alert_count']}")
        
        print(f"\n✅ PRIMARY ACTION:  {incident['primary_action']}")
        print(f"   Description:     {incident['action_description']}")
        print(f"   Automation:      {incident['automation_status']}")
        
        print(f"\n🔄 SECONDARY ACTION: {incident['secondary_action']}")
        secondary_desc = ACTIONS.get(incident['secondary_action'], {}).get('description', 'No description')
        print(f"   Description:     {secondary_desc}")
        
        print(f"\n📋 Threat Intel:    {incident['ti_description']}")
        print(f"💡 Mitigation:      {incident['ti_mitigation']}")
    
    print(f"\n{'='*100}")
    print(f"🚀 Ready for SOAR automation or manual execution")
    print(f"{'='*100}\n")


def export_for_soar(response_df, output_file='response_actions.csv'):
    """
    Export response recommendations in SOAR-friendly format
    
    Args:
        response_df: DataFrame from recommend_response()
        output_file: Output CSV filename
    """
    # Select key columns for SOAR integration
    soar_export = response_df[[
        'source_ip',
        'threat_type',
        'severity',
        'alert_count',
        'avg_confidence',
        'primary_action',
        'secondary_action',
        'action_priority',
        'automation_status',
        'ti_category',
        'ti_risk_level'
    ]].copy()
    
    soar_export.to_csv(output_file, index=False)
    print(f"✅ Exported {len(soar_export)} actions to {output_file} for SOAR integration")
    return output_file


# Example usage for testing
if __name__ == "__main__":
    # Sample enriched incidents (would come from TI enrichment agent)
    sample_enriched = pd.DataFrame({
        'source_ip': ['192.168.1.100', '10.0.0.50', '172.16.0.200', '192.168.5.75'],
        'time_window': ['2026-01-05 10:00:00', '2026-01-05 10:05:00', '2026-01-05 10:10:00', '2026-01-05 10:15:00'],
        'threat_type': ['brute_force', 'malware', 'ransomware', 'data_exfil'],
        'alert_count': [25, 5, 3, 12],
        'avg_confidence': [0.998, 0.995, 0.999, 0.972],
        'severity': ['MEDIUM', 'HIGH', 'HIGH', 'HIGH'],
        'users': [['admin', 'root'], ['john'], ['backup_service'], ['dbadmin']],
        'ti_category': ['Authentication Attack', 'Malicious Software', 'Extortion Malware', 'Data Breach'],
        'ti_description': ['Brute force attack', 'Malware detected', 'Ransomware infection', 'Data exfiltration'],
        'ti_risk_level': ['MEDIUM', 'HIGH', 'HIGH', 'HIGH'],
        'ti_impact': ['Account compromise', 'System compromise', 'Data encryption', 'Data theft'],
        'ti_mitigation': ['Block IP', 'Isolate host', 'Immediate isolation', 'Block connections']
    })
    
    print("\n🧪 Testing Response Recommendation Agent")
    print("="*100)
    
    # Generate recommendations
    response = recommend_response(sample_enriched)
    
    # Print report
    print_response_report(response)
    
    # Export for SOAR
    export_for_soar(response, 'test_soar_actions.csv')
    
    print("\n✅ Response agent test complete!")
