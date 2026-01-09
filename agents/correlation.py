"""
CORRELATION AGENT - Alert Aggregation and Incident Detection
Groups related security alerts into actionable incidents
"""
import pandas as pd
from datetime import timedelta


def correlate_alerts(df, time_window='5min'):
    """
    Correlate security alerts into incidents based on IP, time window, and threat type
    
    Args:
        df: DataFrame with columns [timestamp, source_ip, user, bert_class, bert_confidence, severity]
        time_window: Time window for grouping alerts (e.g., '5min', '10min', '1H')
    
    Returns:
        DataFrame of incidents with aggregated metrics
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()
    
    # Ensure timestamp is datetime
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Handle both 'ip' and 'source_ip' column names
    ip_col = 'source_ip' if 'source_ip' in df.columns else 'ip'
    
    # Filter out normal activity (focus on threats)
    threats = df[df['bert_class'] != 'normal'].copy()
    
    if len(threats) == 0:
        print("⚠️  No threats detected - all logs are normal activity")
        return pd.DataFrame()
    
    # Create time windows
    threats['time_window'] = threats['timestamp'].dt.floor(time_window)
    
    # Group by IP, time window, and threat type
    incidents = threats.groupby([ip_col, 'time_window', 'bert_class']).agg({
        'user': lambda x: list(set(x)),  # Unique users
        'bert_confidence': 'mean',       # Average confidence
        'severity': lambda x: x.mode()[0] if len(x) > 0 else 'MEDIUM',  # Most common severity
        'timestamp': 'count'             # Number of alerts
    }).reset_index()
    
    # Rename columns for clarity
    incidents.rename(columns={
        'bert_class': 'threat_type',
        'timestamp': 'alert_count',
        'bert_confidence': 'avg_confidence',
        'user': 'users',
        ip_col: 'source_ip'  # Standardize to source_ip
    }, inplace=True)
    
    # Add user count
    incidents['user_count'] = incidents['users'].apply(len)
    
    # Sort by severity and alert count
    severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    incidents['severity_rank'] = incidents['severity'].map(severity_order)
    incidents = incidents.sort_values(['severity_rank', 'alert_count'], ascending=[True, False])
    incidents = incidents.drop('severity_rank', axis=1)
    
    return incidents


def get_incident_summary(incidents):
    """
    Generate summary statistics for incidents
    
    Args:
        incidents: DataFrame from correlate_alerts()
    
    Returns:
        Dictionary with summary metrics
    """
    if incidents is None or len(incidents) == 0:
        return {
            'total_incidents': 0,
            'high_severity': 0,
            'medium_severity': 0,
            'low_severity': 0,
            'threat_breakdown': {}
        }
    
    summary = {
        'total_incidents': len(incidents),
        'high_severity': len(incidents[incidents['severity'] == 'HIGH']),
        'medium_severity': len(incidents[incidents['severity'] == 'MEDIUM']),
        'low_severity': len(incidents[incidents['severity'] == 'LOW']),
        'threat_breakdown': incidents['threat_type'].value_counts().to_dict(),
        'avg_alerts_per_incident': incidents['alert_count'].mean(),
        'max_alerts_in_incident': incidents['alert_count'].max(),
    }
    
    return summary


def print_incident_report(incidents, alerts_df):
    """
    Print formatted incident report
    
    Args:
        incidents: DataFrame from correlate_alerts()
        alerts_df: Original alerts DataFrame
    """
    if incidents is None or len(incidents) == 0:
        print("\n📋 No incidents detected")
        return
    
    print("\n" + "="*80)
    print("📋 SECURITY INCIDENTS REPORT")
    print("="*80)
    print(f"{'IP':<16} {'Time Window':<20} {'Users':<6} {'Threat Type':<15} {'Alerts':<8} {'Confidence':<12} {'Severity'}")
    print("-"*80)
    
    for _, inc in incidents.iterrows():
        print(f"{inc['source_ip']:<16} "
              f"{str(inc['time_window']):<20} "
              f"{inc['user_count']:<6} "
              f"{inc['threat_type']:<15} "
              f"{inc['alert_count']:<8} "
              f"{inc['avg_confidence']:<12.3f} "
              f"{inc['severity']}")
    
    # Summary statistics
    summary = get_incident_summary(incidents)
    
    print("\n" + "="*80)
    print("📊 PIPELINE SUMMARY")
    print("="*80)
    print(f"Total Logs Processed:           {len(alerts_df)}")
    print(f"Total Incidents Detected:       {summary['total_incidents']}")
    print(f"Incident Reduction Ratio:    {len(alerts_df)/summary['total_incidents']:.1f}x")
    
    print(f"\nIncident Breakdown by Threat Type:")
    for threat, count in sorted(summary['threat_breakdown'].items(), key=lambda x: x[1], reverse=True):
        print(f"  • {threat:<15}:  {count} incident(s)")
    
    print(f"\nIncident Breakdown by Severity:")
    print(f"  • HIGH           :  {summary['high_severity']} incident(s)")
    print(f"  • MEDIUM         :  {summary['medium_severity']} incident(s)")
    print(f"  • LOW            :  {summary['low_severity']} incident(s)")
    
    # Show top incidents
    print(f"\nTop 3 Highest-Alert Incidents:")
    top_3 = incidents.nlargest(3, 'alert_count')
    for _, inc in top_3.iterrows():
        print(f"  • {inc['source_ip']:<15} | {inc['threat_type']:<12} | {inc['alert_count']:3} alerts | {inc['severity']}")
    
    print("="*80)


if __name__ == "__main__":
    # Test the correlation module
    print("="*80)
    print("🧪 TESTING CORRELATION MODULE")
    print("="*80)
    
    # Create sample data
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range('2026-01-04 10:00', periods=20, freq='1min'),
        'source_ip': ['192.168.1.10']*10 + ['192.168.1.20']*10,
        'user': ['admin']*20,
        'bert_class': ['brute_force']*8 + ['normal']*2 + ['malware']*10,
        'bert_confidence': [0.95]*20,
        'severity': ['MEDIUM']*10 + ['HIGH']*10
    })
    
    print(f"\n📊 Sample data: {len(sample_data)} alerts")
    
    # Run correlation
    incidents = correlate_alerts(sample_data, time_window='5min')
    
    # Print report
    print_incident_report(incidents, sample_data)
    
    print("\n✅ Correlation module test complete!")