"""
Test BERT pipeline with your real security logs
"""
import pandas as pd
from agents.bert_detection import bert_detect
from agents.correlation import correlate_alerts, print_incident_report

# ==============================================================================
# OPTION 1: Load from CSV file
# ==============================================================================
# Your CSV must have at least these columns: 'message', 'timestamp', 'source_ip', 'user'
# Example format:
# timestamp,source_ip,user,message
# 2026-01-03 08:00:00,192.168.1.100,admin,Failed login attempt
# 2026-01-03 08:00:05,192.168.1.100,admin,Failed login attempt

def test_from_csv(csv_file):
    """Load real logs from CSV and run full pipeline"""
    print("="*80)
    print("🔍 TESTING WITH REAL LOGS")
    print("="*80)
    
    # Load your logs
    print(f"\n📂 Loading logs from {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df)} logs")
    
    # Required columns check
    required = ['message', 'timestamp', 'source_ip', 'user']
    missing = [col for col in required if col not in df.columns]
    if missing:
        print(f"❌ Missing required columns: {missing}")
        print(f"   Your columns: {list(df.columns)}")
        return
    
    # Step 1: BERT Classification
    print("\n🤖 Running BERT detection...")
    df = bert_detect(df)
    
    # Show classification results
    print("\n📊 CLASSIFICATION RESULTS:")
    print("-"*80)
    print(df[['message', 'bert_class', 'bert_confidence', 'severity']].head(10))
    
    print("\n📈 Threat Distribution:")
    print(df['bert_class'].value_counts())
    
    # Show severity breakdown
    print("\n⚠️  Severity Breakdown:")
    print(df['severity'].value_counts())
    
    # Show high confidence threats
    high_conf = df[df['bert_confidence'] > 0.95]
    print(f"\n🎯 High Confidence Detections (>{0.95:.0%}): {len(high_conf)}")
    
    # If actual_threat column exists (from generated logs), show accuracy
    if 'actual_threat' in df.columns:
        accuracy = (df['bert_class'] == df['actual_threat']).mean()
        print(f"\n📊 Model Accuracy: {accuracy:.1%}")
    
    # Step 2: CORRELATION
    print("\n🔗 Step 2: Correlating alerts into incidents...")
    incidents = correlate_alerts(df, time_window='5min')
    
    if len(incidents) > 0:
        print(f"✅ Created {len(incidents)} incidents from {len(df)} alerts")
        
        # Print full incident report
        print_incident_report(incidents, df)
    else:
        print("⚠️  No threat incidents detected (all logs are normal)")
    
    print("\n" + "="*80)
    print("✅ FULL PIPELINE COMPLETE!")
    print("="*80)
    
    return df, incidents


# ==============================================================================
# OPTION 2: Test with manual log entries
# ==============================================================================
def test_manual_logs():
    """Test with manually entered logs"""
    print("="*80)
    print("🔍 TESTING WITH MANUAL LOGS")
    print("="*80)
    
    # Create sample logs (REPLACE THESE with your real logs)
    logs = [
        "Failed password for admin from 192.168.1.50",
        "Failed password for admin from 192.168.1.50",
        "Failed password for admin from 192.168.1.50",
        "User successfully authenticated",
        "Suspicious .exe file detected in temp directory",
        "Unusual outbound traffic to external IP 203.0.113.5",
    ]
    
    df = pd.DataFrame({
        'message': logs,
        'timestamp': pd.date_range('2026-01-04 10:00:00', periods=len(logs), freq='1min'),
        'source_ip': ['192.168.1.50', '192.168.1.50', '192.168.1.50', '192.168.1.100', '192.168.1.100', '192.168.1.100'],
        'user': ['admin', 'admin', 'admin', 'john', 'system', 'system']
    })
    
    print(f"\n📊 Testing with {len(df)} log entries...")
    
    # Run BERT detection
    df = bert_detect(df)
    
    print("\n🎯 RESULTS:")
    print("-"*80)
    for idx, row in df.iterrows():
        print(f"{row['bert_class']:15s} | Conf: {row['bert_confidence']:.3f} | {row['severity']:6s} | {row['message'][:60]}")
    
    return df


# ==============================================================================
# OPTION 3: Test single log message
# ==============================================================================
def test_single_message(message):
    """Quick test for a single log message"""
    df = pd.DataFrame({
        'message': [message],
        'timestamp': [pd.Timestamp.now()],
        'source_ip': ['0.0.0.0'],
        'user': ['unknown']
    })
    
    result = bert_detect(df)
    
    print("\n" + "="*80)
    print(f"📝 Log: {message}")
    print("-"*80)
    print(f"🎯 Classification: {result['bert_class'].iloc[0]}")
    print(f"📊 Confidence: {result['bert_confidence'].iloc[0]:.1%}")
    print(f"⚠️  Severity: {result['severity'].iloc[0]}")
    print("="*80)
    
    return result


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    import sys
    
    print("\n🔧 REAL LOG TESTING OPTIONS:")
    print("="*80)
    print("1. Test from CSV file:    python test_real_logs.py csv YOUR_FILE.csv")
    print("2. Test manual logs:      python test_real_logs.py manual")
    print("3. Test single message:   python test_real_logs.py single 'Your log message here'")
    print("="*80)
    
    if len(sys.argv) < 2:
        # Default: run manual test
        print("\n[Running default: Manual log test]\n")
        test_manual_logs()
    
    elif sys.argv[1] == 'csv' and len(sys.argv) >= 3:
        csv_file = sys.argv[2]
        test_from_csv(csv_file)
    
    elif sys.argv[1] == 'manual':
        test_manual_logs()
    
    elif sys.argv[1] == 'single' and len(sys.argv) >= 3:
        message = ' '.join(sys.argv[2:])
        test_single_message(message)
    
    else:
        print("❌ Invalid arguments. See options above.")
