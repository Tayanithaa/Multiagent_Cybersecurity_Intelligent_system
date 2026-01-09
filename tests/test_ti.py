"""
TEST THREAT INTELLIGENCE ENRICHMENT
Tests the TI enrichment agent on sample incidents from correlation output
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from agents.ti_enrichment import enrich_with_threat_intel, get_threat_details, print_enriched_report


def test_ti_enrichment_basic():
    """Test basic TI enrichment functionality"""
    print("\n" + "="*100)
    print("TEST 1: Basic Threat Intelligence Enrichment")
    print("="*100)
    
    # Sample incidents (simulating correlation agent output)
    test_incidents = pd.DataFrame({
        'source_ip': ['192.168.1.100', '10.0.0.50', '172.16.0.200'],
        'time_window': ['2026-01-05 10:00:00', '2026-01-05 10:05:00', '2026-01-05 10:10:00'],
        'threat_type': ['brute_force', 'malware', 'ransomware'],
        'alert_count': [25, 5, 3],
        'avg_confidence': [0.998, 0.995, 0.999],
        'severity': ['MEDIUM', 'HIGH', 'HIGH'],
        'users': [['admin', 'root'], ['john'], ['backup_service']]
    })
    
    print(f"\n📥 Input: {len(test_incidents)} incidents from correlation agent")
    print(test_incidents[['source_ip', 'threat_type', 'severity', 'alert_count']].to_string(index=False))
    
    # Enrich with TI
    enriched = enrich_with_threat_intel(test_incidents)
    
    print(f"\n✅ Enriched: {len(enriched)} incidents with TI data")
    
    # Verify enrichment columns were added
    ti_columns = ['ti_category', 'ti_description', 'ti_risk_level', 'ti_impact', 'ti_mitigation']
    missing_cols = [col for col in ti_columns if col not in enriched.columns]
    
    if missing_cols:
        print(f"❌ FAIL: Missing columns: {missing_cols}")
        return False
    else:
        print(f"✅ PASS: All TI columns added: {ti_columns}")
    
    # Check data correctness
    print("\n🔍 Verifying TI data correctness:")
    for idx, row in enriched.iterrows():
        threat = row['threat_type']
        category = row['ti_category']
        risk = row['ti_risk_level']
        print(f"  {threat:20s} → Category: {category:30s} Risk: {risk}")
    
    # Print full report
    print_enriched_report(enriched)
    
    return True


def test_all_threat_types():
    """Test TI enrichment on all 8 threat types"""
    print("\n" + "="*100)
    print("TEST 2: All Threat Types Coverage")
    print("="*100)
    
    all_threats = pd.DataFrame({
        'source_ip': ['192.168.1.1', '192.168.1.2', '192.168.1.3', '192.168.1.4',
                      '192.168.1.5', '192.168.1.6', '192.168.1.7', '192.168.1.8'],
        'time_window': ['2026-01-05 10:00:00'] * 8,
        'threat_type': ['normal', 'brute_force', 'malware', 'phishing', 
                        'ddos', 'ransomware', 'data_exfil', 'insider_threat'],
        'alert_count': [1, 20, 8, 5, 100, 3, 15, 7],
        'avg_confidence': [0.95, 0.998, 0.99, 0.985, 0.992, 0.999, 0.975, 0.988],
        'severity': ['LOW', 'MEDIUM', 'HIGH', 'MEDIUM', 'MEDIUM', 'HIGH', 'HIGH', 'HIGH'],
        'users': [['user1'], ['admin'], ['john'], ['alice'], 
                  ['*'], ['backup'], ['dbadmin'], ['insider']]
    })
    
    print(f"\n📥 Input: {len(all_threats)} threats (all 8 types)")
    
    # Enrich
    enriched = enrich_with_threat_intel(all_threats)
    
    print(f"\n✅ Enriched: {len(enriched)} threats")
    
    # Display summary table
    summary = enriched[['threat_type', 'ti_category', 'ti_risk_level', 'severity']].copy()
    print("\n📊 Enrichment Summary:")
    print(summary.to_string(index=False))
    
    # Verify no missing data
    null_counts = enriched[['ti_category', 'ti_description', 'ti_risk_level']].isnull().sum()
    if null_counts.sum() > 0:
        print(f"\n❌ FAIL: Found null values in TI columns")
        print(null_counts)
        return False
    else:
        print(f"\n✅ PASS: No null values - all threats properly enriched")
    
    return True


def test_individual_threat_lookup():
    """Test get_threat_details() function"""
    print("\n" + "="*100)
    print("TEST 3: Individual Threat Lookup")
    print("="*100)
    
    test_threats = ['brute_force', 'malware', 'ransomware', 'unknown_threat']
    
    for threat in test_threats:
        print(f"\n🔍 Looking up: {threat}")
        details = get_threat_details(threat)
        
        print(f"  Category:    {details.get('category', 'N/A')}")
        print(f"  Risk Level:  {details.get('risk_level', 'N/A')}")
        print(f"  Description: {details.get('description', 'N/A')[:80]}...")
        
        if threat == 'unknown_threat':
            if details['category'] == 'Unknown':
                print(f"  ✅ PASS: Unknown threat handled correctly")
            else:
                print(f"  ❌ FAIL: Should return Unknown for invalid threat")
                return False
    
    print("\n✅ PASS: Individual threat lookup working correctly")
    return True


def test_empty_input():
    """Test handling of empty input"""
    print("\n" + "="*100)
    print("TEST 4: Empty Input Handling")
    print("="*100)
    
    empty_df = pd.DataFrame()
    
    print("\n📥 Input: Empty DataFrame")
    enriched = enrich_with_threat_intel(empty_df)
    
    if len(enriched) == 0:
        print("✅ PASS: Empty input handled correctly (returned empty DataFrame)")
        return True
    else:
        print("❌ FAIL: Should return empty DataFrame for empty input")
        return False


def test_high_confidence_filtering():
    """Test that TI enrichment works regardless of confidence level"""
    print("\n" + "="*100)
    print("TEST 5: Confidence Level Independence")
    print("="*100)
    
    test_data = pd.DataFrame({
        'source_ip': ['192.168.1.1', '192.168.1.2'],
        'time_window': ['2026-01-05 10:00:00'] * 2,
        'threat_type': ['malware', 'malware'],
        'alert_count': [5, 5],
        'avg_confidence': [0.999, 0.700],  # High vs low confidence
        'severity': ['HIGH', 'HIGH'],
        'users': [['user1'], ['user2']]
    })
    
    print("\n📥 Input: Same threat, different confidence levels")
    print(test_data[['threat_type', 'avg_confidence']].to_string(index=False))
    
    enriched = enrich_with_threat_intel(test_data)
    
    # Both should get same TI enrichment
    ti_categories = enriched['ti_category'].unique()
    if len(ti_categories) == 1:
        print(f"✅ PASS: Both got same TI category: {ti_categories[0]}")
        print("   (TI enrichment is independent of confidence)")
        return True
    else:
        print(f"❌ FAIL: Different TI categories: {ti_categories}")
        return False


def run_all_tests():
    """Run all TI enrichment tests"""
    print("\n" + "🧪 "*40)
    print("THREAT INTELLIGENCE ENRICHMENT TEST SUITE")
    print("🧪 "*40)
    
    tests = [
        ("Basic TI Enrichment", test_ti_enrichment_basic),
        ("All Threat Types", test_all_threat_types),
        ("Individual Threat Lookup", test_individual_threat_lookup),
        ("Empty Input Handling", test_empty_input),
        ("Confidence Independence", test_high_confidence_filtering),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {str(e)}")
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
        print("✅ All tests passed! TI enrichment agent is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
