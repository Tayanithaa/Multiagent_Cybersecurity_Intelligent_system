import pandas as pd
import sys
import os

# Add agents path to import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

from bert_detection import bert_detect
from correlation import correlate_alerts, print_incident_report


def test_correlation():
    """End-to-end test: Full pipeline from logs → BERT → Incidents"""
    
    print("\n" + "="*80)
    print("🧪 END-TO-END CORRELATION PIPELINE TEST")
    print("="*80)
    
    # Load sample logs
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_logs.csv')
    df = pd.read_csv(data_path)
    
    print(f"\n📊 Step 1: Loaded {len(df)} logs from sample_logs.csv")
    
    # Step 2: Run BERT detection
    print("🚀 Step 2: Running BERT classification...")
    alerts_df = bert_detect(df)
    print(f"✅ Added 3 columns: bert_class, bert_confidence, severity")
    
    # Step 3: Correlate into incidents
    print("🔗 Step 3: Correlating alerts into incidents (5-min windows)...")
    incidents_df = correlate_alerts(alerts_df, time_window='5min')
    
    print(f"✅ Created {len(incidents_df)} incident(s) from {len(alerts_df)} alerts")
    
    # Verify incidents were created
    assert len(incidents_df) > 0, "❌ No incidents created!"
    print("✅ Incident creation successful")
    
    # Display incidents using the print function
    print_incident_report(incidents_df, alerts_df)
    
    # Validate pipeline
    print("\n" + "="*80)
    print("✅ VALIDATION CHECKS")
    print("="*80)
    
    checks = [
        ("Required columns in incidents", all(col in incidents_df.columns for col in ['source_ip', 'threat_type', 'alert_count', 'severity', 'avg_confidence'])),
        ("All incidents have severity", incidents_df['severity'].isnull().sum() == 0),
        ("Alert counts are positive", (incidents_df['alert_count'] > 0).all()),
        ("Confidence scores valid", (incidents_df['avg_confidence'] >= 0).all() and (incidents_df['avg_confidence'] <= 1).all()),
        ("At least 1 incident created", len(incidents_df) >= 1),
    ]
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        assert result, f"Validation failed: {check_name}"
    
    print("\n" + "="*80)
    print("✅ PASSED - END-TO-END PIPELINE SUCCESSFUL!")
    print("="*80 + "\n")
    
    return alerts_df, incidents_df


if __name__ == "__main__":
    alerts_df, incidents_df = test_correlation()
