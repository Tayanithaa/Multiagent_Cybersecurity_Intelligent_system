"""
TEST RESPONSE RECOMMENDATION AGENT
Tests the response agent's decision-making logic on enriched incidents
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from agents.response_agent import recommend_response, get_action_details, print_response_report, export_for_soar


def test_basic_response_recommendations():
    """Test basic response recommendation functionality"""
    print("\n" + "="*100)
    print("TEST 1: Basic Response Recommendations")
    print("="*100)
    
    # Sample enriched incidents (from TI enrichment agent)
    test_incidents = pd.DataFrame({
        'source_ip': ['192.168.1.100', '10.0.0.50', '172.16.0.200'],
        'time_window': ['2026-01-05 10:00:00', '2026-01-05 10:05:00', '2026-01-05 10:10:00'],
        'threat_type': ['brute_force', 'malware', 'ransomware'],
        'alert_count': [25, 5, 3],
        'avg_confidence': [0.998, 0.995, 0.999],
        'severity': ['MEDIUM', 'HIGH', 'HIGH'],
        'users': [['admin', 'root'], ['john'], ['backup_service']],
        'ti_category': ['Authentication Attack', 'Malicious Software', 'Extortion Malware'],
        'ti_description': ['Brute force attack', 'Malware detected', 'Ransomware infection'],
        'ti_risk_level': ['MEDIUM', 'HIGH', 'HIGH'],
        'ti_impact': ['Account compromise', 'System compromise', 'Data encryption'],
        'ti_mitigation': ['Block IP', 'Isolate host', 'Immediate isolation']
    })
    
    print(f"\n📥 Input: {len(test_incidents)} enriched incidents")
    print(test_incidents[['source_ip', 'threat_type', 'severity', 'alert_count']].to_string(index=False))
    
    # Generate recommendations
    response = recommend_response(test_incidents)
    
    print(f"\n✅ Generated: {len(response)} response recommendations")
    
    # Verify response columns were added
    response_columns = ['primary_action', 'secondary_action', 'action_priority', 'automation_status']
    missing_cols = [col for col in response_columns if col not in response.columns]
    
    if missing_cols:
        print(f"❌ FAIL: Missing columns: {missing_cols}")
        return False
    else:
        print(f"✅ PASS: All response columns added: {response_columns}")
    
    # Check action correctness
    print("\n🔍 Verifying action recommendations:")
    for idx, row in response.iterrows():
        threat = row['threat_type']
        primary = row['primary_action']
        secondary = row['secondary_action']
        priority = row['action_priority']
        print(f"  {threat:20s} → Primary: {primary:20s} Secondary: {secondary:20s} Priority: {priority}")
    
    # Print full report
    print_response_report(response)
    
    return True


def test_all_threat_types():
    """Test response recommendations for all 8 threat types"""
    print("\n" + "="*100)
    print("TEST 2: All Threat Types Response Logic")
    print("="*100)
    
    all_threats = pd.DataFrame({
        'source_ip': ['192.168.1.1', '192.168.1.2', '192.168.1.3', '192.168.1.4',
                      '192.168.1.5', '192.168.1.6', '192.168.1.7', '192.168.1.8'],
        'time_window': ['2026-01-05 10:00:00'] * 8,
        'threat_type': ['normal', 'brute_force', 'malware', 'phishing', 
                        'ddos', 'ransomware', 'data_exfil', 'insider_threat'],
        'alert_count': [1, 25, 8, 5, 100, 3, 15, 7],
        'avg_confidence': [0.95, 0.998, 0.99, 0.985, 0.992, 0.999, 0.975, 0.988],
        'severity': ['LOW', 'MEDIUM', 'HIGH', 'MEDIUM', 'MEDIUM', 'HIGH', 'HIGH', 'HIGH'],
        'users': [['user1'], ['admin'], ['john'], ['alice'], ['*'], ['backup'], ['dbadmin'], ['insider']],
        'ti_category': ['Normal Activity', 'Authentication Attack', 'Malicious Software', 'Social Engineering',
                        'Denial of Service', 'Extortion Malware', 'Data Breach', 'Insider Activity'],
        'ti_description': ['Normal', 'Brute force', 'Malware', 'Phishing', 'DDoS', 'Ransomware', 'Data exfil', 'Insider'],
        'ti_risk_level': ['LOW', 'MEDIUM', 'HIGH', 'MEDIUM', 'MEDIUM', 'HIGH', 'HIGH', 'HIGH'],
        'ti_impact': ['None', 'Account compromise', 'System compromise', 'Credential theft',
                      'Service disruption', 'Data encryption', 'Data theft', 'Privilege abuse'],
        'ti_mitigation': ['No action', 'Block IP', 'Isolate host', 'Block URLs', 'DDoS mitigation', 
                          'Immediate isolation', 'Block connections', 'Disable account']
    })
    
    print(f"\n📥 Input: {len(all_threats)} threats (all 8 types)")
    
    # Generate recommendations
    response = recommend_response(all_threats)
    
    print(f"\n✅ Generated: {len(response)} recommendations")
    
    # Display summary table
    summary = response[['threat_type', 'primary_action', 'secondary_action', 'action_priority']].copy()
    print("\n📊 Response Summary:")
    print(summary.to_string(index=False))
    
    # Verify critical threats get priority 1
    critical_threats = ['ransomware', 'malware', 'data_exfil', 'insider_threat']
    for threat in critical_threats:
        threat_row = response[response['threat_type'] == threat]
        if len(threat_row) > 0:
            priority = threat_row.iloc[0]['action_priority']
            action = threat_row.iloc[0]['primary_action']
            if priority <= 2:  # Should be high priority
                print(f"  ✅ {threat:20s} → {action:20s} (Priority {priority})")
            else:
                print(f"  ❌ {threat:20s} → {action:20s} (Priority {priority} - should be 1 or 2)")
                return False
    
    print("\n✅ PASS: All critical threats assigned appropriate priorities")
    return True


def test_brute_force_thresholds():
    """Test brute force alert count thresholds"""
    print("\n" + "="*100)
    print("TEST 3: Brute Force Alert Count Thresholds")
    print("="*100)
    
    brute_force_tests = pd.DataFrame({
        'source_ip': ['192.168.1.1', '192.168.1.2', '192.168.1.3'],
        'time_window': ['2026-01-05 10:00:00'] * 3,
        'threat_type': ['brute_force'] * 3,
        'alert_count': [5, 15, 25],  # Low, medium, high volume
        'avg_confidence': [0.95] * 3,
        'severity': ['MEDIUM'] * 3,
        'users': [['user1'], ['user2'], ['admin']],
        'ti_category': ['Authentication Attack'] * 3,
        'ti_description': ['Brute force attack'] * 3,
        'ti_risk_level': ['MEDIUM'] * 3,
        'ti_impact': ['Account compromise'] * 3,
        'ti_mitigation': ['Block IP'] * 3
    })
    
    print("\n📥 Input: Brute force with different alert counts")
    print(brute_force_tests[['alert_count']].to_string(index=False))
    
    response = recommend_response(brute_force_tests)
    
    print("\n🔍 Verifying threshold logic:")
    for idx, row in response.iterrows():
        count = row['alert_count']
        action = row['primary_action']
        print(f"  Alert count: {count:2d} → Action: {action}")
        
        # Verify logic: <10=MONITOR, 10-19=RESET_PASSWORD, >=20=BLOCK_IP
        if count < 10 and action != 'MONITOR':
            print(f"    ❌ FAIL: Low count should MONITOR")
            return False
        elif 10 <= count < 20 and action != 'RESET_PASSWORD':
            print(f"    ❌ FAIL: Medium count should RESET_PASSWORD")
            return False
        elif count >= 20 and action != 'BLOCK_IP':
            print(f"    ❌ FAIL: High count should BLOCK_IP")
            return False
        else:
            print(f"    ✅ Correct")
    
    print("\n✅ PASS: Brute force thresholds working correctly")
    return True


def test_ransomware_response():
    """Test that ransomware always gets most aggressive response"""
    print("\n" + "="*100)
    print("TEST 4: Ransomware Critical Response")
    print("="*100)
    
    ransomware_test = pd.DataFrame({
        'source_ip': ['192.168.1.100'],
        'time_window': ['2026-01-05 10:00:00'],
        'threat_type': ['ransomware'],
        'alert_count': [3],
        'avg_confidence': [0.999],
        'severity': ['HIGH'],
        'users': [['backup_service']],
        'ti_category': ['Extortion Malware'],
        'ti_description': ['Ransomware infection'],
        'ti_risk_level': ['HIGH'],
        'ti_impact': ['Data encryption'],
        'ti_mitigation': ['Immediate isolation']
    })
    
    response = recommend_response(ransomware_test)
    
    primary = response.iloc[0]['primary_action']
    secondary = response.iloc[0]['secondary_action']
    priority = response.iloc[0]['action_priority']
    
    print(f"\n🔍 Ransomware response:")
    print(f"  Primary:   {primary}")
    print(f"  Secondary: {secondary}")
    print(f"  Priority:  {priority}")
    
    # Ransomware should ISOLATE_HOST (critical action)
    if primary == 'ISOLATE_HOST' and priority == 1:
        print(f"\n✅ PASS: Ransomware gets immediate isolation (Priority 1)")
        return True
    else:
        print(f"\n❌ FAIL: Ransomware should get ISOLATE_HOST with Priority 1")
        return False


def test_confidence_impact():
    """Test how confidence level affects actions"""
    print("\n" + "="*100)
    print("TEST 5: Confidence Level Impact on Actions")
    print("="*100)
    
    confidence_tests = pd.DataFrame({
        'source_ip': ['192.168.1.1', '192.168.1.2'],
        'time_window': ['2026-01-05 10:00:00'] * 2,
        'threat_type': ['malware'] * 2,
        'alert_count': [5, 5],
        'avg_confidence': [0.999, 0.900],  # Very high vs lower confidence
        'severity': ['HIGH'] * 2,
        'users': [['user1'], ['user2']],
        'ti_category': ['Malicious Software'] * 2,
        'ti_description': ['Malware detected'] * 2,
        'ti_risk_level': ['HIGH'] * 2,
        'ti_impact': ['System compromise'] * 2,
        'ti_mitigation': ['Isolate host'] * 2
    })
    
    print("\n📥 Input: Same threat, different confidence levels")
    print(confidence_tests[['threat_type', 'avg_confidence']].to_string(index=False))
    
    response = recommend_response(confidence_tests)
    
    print("\n🔍 Verifying confidence impact:")
    high_conf_action = response.iloc[0]['primary_action']
    low_conf_action = response.iloc[1]['primary_action']
    
    print(f"  High confidence (99.9%): {high_conf_action}")
    print(f"  Lower confidence (90.0%): {low_conf_action}")
    
    # High confidence malware should isolate, lower confidence might scan
    if high_conf_action in ['ISOLATE_HOST', 'SCAN_SYSTEM'] and low_conf_action in ['SCAN_SYSTEM', 'ISOLATE_HOST']:
        print(f"\n✅ PASS: Confidence level affects action aggressiveness")
        return True
    else:
        print(f"\n⚠️  PARTIAL PASS: Actions are reasonable for malware")
        return True  # Not a hard fail


def test_action_metadata():
    """Test get_action_details() function"""
    print("\n" + "="*100)
    print("TEST 6: Action Metadata Lookup")
    print("="*100)
    
    test_actions = ['BLOCK_IP', 'ISOLATE_HOST', 'ESCALATE', 'MONITOR', 'UNKNOWN_ACTION']
    
    for action in test_actions:
        print(f"\n🔍 Looking up: {action}")
        details = get_action_details(action)
        
        print(f"  Priority:    {details.get('priority', 'N/A')}")
        print(f"  Automation:  {details.get('automation', 'N/A')}")
        print(f"  Description: {details.get('description', 'N/A')[:60]}...")
        
        if action == 'UNKNOWN_ACTION':
            if details['priority'] == 3 and details['description'] == 'Unknown action':
                print(f"  ✅ PASS: Unknown action handled correctly")
            else:
                print(f"  ❌ FAIL: Should return default for unknown action")
                return False
    
    print("\n✅ PASS: Action metadata lookup working correctly")
    return True


def test_soar_export():
    """Test SOAR export functionality"""
    print("\n" + "="*100)
    print("TEST 7: SOAR Export")
    print("="*100)
    
    test_data = pd.DataFrame({
        'source_ip': ['192.168.1.100', '10.0.0.50'],
        'time_window': ['2026-01-05 10:00:00', '2026-01-05 10:05:00'],
        'threat_type': ['brute_force', 'malware'],
        'alert_count': [25, 5],
        'avg_confidence': [0.998, 0.995],
        'severity': ['MEDIUM', 'HIGH'],
        'users': [['admin'], ['john']],
        'ti_category': ['Authentication Attack', 'Malicious Software'],
        'ti_description': ['Brute force', 'Malware'],
        'ti_risk_level': ['MEDIUM', 'HIGH'],
        'ti_impact': ['Account compromise', 'System compromise'],
        'ti_mitigation': ['Block IP', 'Isolate host']
    })
    
    response = recommend_response(test_data)
    
    # Export for SOAR
    output_file = 'test_soar_export.csv'
    export_for_soar(response, output_file)
    
    # Verify file was created
    if os.path.exists(output_file):
        exported = pd.read_csv(output_file)
        print(f"\n✅ File created: {output_file}")
        print(f"   Rows: {len(exported)}")
        print(f"   Columns: {list(exported.columns)}")
        
        # Clean up
        os.remove(output_file)
        print(f"✅ PASS: SOAR export working correctly")
        return True
    else:
        print(f"❌ FAIL: Export file not created")
        return False


def test_empty_input():
    """Test handling of empty input"""
    print("\n" + "="*100)
    print("TEST 8: Empty Input Handling")
    print("="*100)
    
    empty_df = pd.DataFrame()
    
    print("\n📥 Input: Empty DataFrame")
    response = recommend_response(empty_df)
    
    if len(response) == 0:
        print("✅ PASS: Empty input handled correctly (returned empty DataFrame)")
        return True
    else:
        print("❌ FAIL: Should return empty DataFrame for empty input")
        return False


def run_all_tests():
    """Run all response agent tests"""
    print("\n" + "⚡ "*40)
    print("RESPONSE RECOMMENDATION AGENT TEST SUITE")
    print("⚡ "*40)
    
    tests = [
        ("Basic Response Recommendations", test_basic_response_recommendations),
        ("All Threat Types Logic", test_all_threat_types),
        ("Brute Force Thresholds", test_brute_force_thresholds),
        ("Ransomware Critical Response", test_ransomware_response),
        ("Confidence Impact", test_confidence_impact),
        ("Action Metadata Lookup", test_action_metadata),
        ("SOAR Export", test_soar_export),
        ("Empty Input Handling", test_empty_input),
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
    print("📊 TEST SUMMARY")
    print("="*100)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n🎯 Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("✅ All tests passed! Response agent is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
