"""
END-TO-END INTEGRATION TEST
Tests the complete pipeline: BERT Detection → Correlation → TI Enrichment → Response
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from agents.bert_detection import bert_detect
from agents.correlation import correlate_alerts
from agents.ti_enrichment import enrich_with_threat_intel
from agents.response_agent import recommend_response, print_response_report


def test_full_pipeline():
    """Test complete agent pipeline"""
    print("\n" + "="*100)
    print("🔗 FULL MULTI-AGENT PIPELINE TEST")
    print("="*100)
    
    # Load sample logs
    print("\n📂 STEP 1: Loading sample logs...")
    try:
        df = pd.read_csv('data/sample_logs.csv')
        print(f"✅ Loaded {len(df)} logs")
        print(f"   Columns: {list(df.columns)}")
    except FileNotFoundError:
        print("❌ sample_logs.csv not found - using synthetic data")
        df = pd.DataFrame({
            'timestamp': pd.date_range('2026-01-05 10:00:00', periods=50, freq='30s'),
            'source_ip': ['192.168.1.100']*25 + ['10.0.0.50']*10 + ['172.16.0.200']*5 + ['192.168.5.75']*10,
            'user': ['admin']*25 + ['john']*10 + ['backup']*5 + ['dbadmin']*10,
            'message': [
                'Failed password for admin from 192.168.1.100'
            ]*25 + [
                'Trojan detected: malware.exe'
            ]*10 + [
                'Ransomware activity detected: files encrypted'
            ]*5 + [
                'Large data transfer to external IP detected'
            ]*10
        })
    
    print(f"\n📊 Sample of raw logs:")
    # Handle different column names
    display_cols = []
    for col in ['timestamp', 'source_ip', 'ip', 'user', 'message', 'raw_message']:
        if col in df.columns:
            display_cols.append(col)
    print(df.head(3)[display_cols[:4]].to_string(index=False))
    
    # AGENT 1: BERT Detection
    print("\n🤖 STEP 2: Running BERT Detection Agent...")
    print("   (This may take a moment if loading model for first time)")
    
    try:
        classified = bert_detect(df)
        print(f"✅ Classified {len(classified)} logs")
        
        # Show classification distribution
        class_counts = classified['bert_class'].value_counts()
        print(f"\n   Classification breakdown:")
        for threat, count in class_counts.items():
            print(f"   - {threat:20s}: {count:3d} alerts")
    except Exception as e:
        print(f"❌ BERT detection failed: {e}")
        print("   (Model may not be trained yet - run python training/train_bert_model.py)")
        return False
    
    # AGENT 2: Correlation
    print("\n🔗 STEP 3: Running Correlation Agent...")
    incidents = correlate_alerts(classified, time_window='5min')
    
    if len(incidents) == 0:
        print("⚠️  No security incidents detected (all normal activity)")
        return True
    
    print(f"✅ Correlated into {len(incidents)} security incidents")
    print(f"   Alert reduction: {len(classified)}/{len(incidents)} = {len(classified)/len(incidents):.1f}x")
    
    # AGENT 3: Threat Intelligence Enrichment
    print("\n🔍 STEP 4: Running TI Enrichment Agent...")
    enriched = enrich_with_threat_intel(incidents)
    print(f"✅ Enriched {len(enriched)} incidents with threat intelligence")
    
    # AGENT 4: Response Recommendations
    print("\n⚡ STEP 5: Running Response Recommendation Agent...")
    response = recommend_response(enriched)
    print(f"✅ Generated {len(response)} response recommendations")
    
    # Display final results
    print("\n" + "="*100)
    print("📋 FINAL RESULTS - TOP 5 PRIORITY INCIDENTS")
    print("="*100)
    
    top_5 = response.head(5)
    for idx, incident in top_5.iterrows():
        priority_emoji = '🔴' if incident['action_priority'] == 1 else '🟠' if incident['action_priority'] == 2 else '🟡'
        print(f"\n{priority_emoji} Priority {incident['action_priority']} | {incident['threat_type'].upper()}")
        print(f"   Source IP:    {incident['source_ip']}")
        print(f"   Alerts:       {incident['alert_count']} alerts")
        print(f"   Confidence:   {incident['avg_confidence']:.1%}")
        print(f"   Action:       {incident['primary_action']} → {incident['secondary_action']}")
        print(f"   Description:  {incident['ti_description'][:70]}")
    
    # Pipeline summary
    print("\n" + "="*100)
    print("✅ PIPELINE COMPLETE")
    print("="*100)
    print(f"Raw logs:           {len(df)}")
    print(f"Classified alerts:  {len(classified)}")
    print(f"Correlated incidents: {len(incidents)}")
    print(f"Enriched with TI:   {len(enriched)}")
    print(f"Response actions:   {len(response)}")
    print(f"\n🎯 Ready for SOAR integration or SOC analyst review")
    
    return True


def test_member1_member2_integration():
    """Test that Member 1 and Member 2 outputs are compatible"""
    print("\n" + "="*100)
    print("🤝 MEMBER 1 + MEMBER 2 INTEGRATION TEST")
    print("="*100)
    
    print("\n✅ Testing data flow between agents:")
    
    # Simulate Member 1 output (correlation)
    member1_output = pd.DataFrame({
        'source_ip': ['192.168.1.100'],
        'time_window': ['2026-01-05 10:00:00'],
        'threat_type': ['brute_force'],
        'alert_count': [25],
        'avg_confidence': [0.998],
        'severity': ['MEDIUM'],
        'users': [['admin', 'root']]
    })
    
    print("   Member 1 (Correlation) output:")
    print(f"   - Columns: {list(member1_output.columns)}")
    print(f"   - Rows: {len(member1_output)}")
    
    # Pass to Member 2 Agent 1 (TI Enrichment)
    enriched = enrich_with_threat_intel(member1_output)
    print(f"\n   Member 2 Agent 1 (TI Enrichment) output:")
    print(f"   - Added columns: ['ti_category', 'ti_description', 'ti_risk_level', 'ti_impact', 'ti_mitigation']")
    print(f"   - Rows: {len(enriched)}")
    
    # Pass to Member 2 Agent 2 (Response)
    response = recommend_response(enriched)
    print(f"\n   Member 2 Agent 2 (Response) output:")
    print(f"   - Added columns: ['primary_action', 'secondary_action', 'action_priority', 'automation_status']")
    print(f"   - Rows: {len(response)}")
    
    # Verify complete pipeline
    required_columns = [
        'source_ip', 'threat_type', 'severity', 'alert_count',  # Member 1
        'ti_category', 'ti_risk_level',  # Member 2 TI
        'primary_action', 'action_priority'  # Member 2 Response
    ]
    
    missing = [col for col in required_columns if col not in response.columns]
    
    if missing:
        print(f"\n❌ FAIL: Missing columns: {missing}")
        return False
    else:
        print(f"\n✅ PASS: All required columns present")
        print(f"   Full pipeline: Member 1 → Member 2 TI → Member 2 Response")
        return True


def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "🔗 "*40)
    print("MULTI-AGENT INTEGRATION TEST SUITE")
    print("🔗 "*40)
    
    tests = [
        ("Member 1 + Member 2 Integration", test_member1_member2_integration),
        ("Full 4-Agent Pipeline", test_full_pipeline),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*100)
    print("📊 INTEGRATION TEST SUMMARY")
    print("="*100)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n🎯 Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n✅ INTEGRATION COMPLETE!")
        print("   Member 1 (ML Detection) + Member 2 (Decision Making) are fully integrated")
        print("   Ready for Member 3 to build backend/frontend")
        return True
    else:
        print("\n⚠️  Some integration issues detected")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
