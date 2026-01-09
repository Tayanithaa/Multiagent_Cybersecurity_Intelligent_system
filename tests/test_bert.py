import pandas as pd
import sys
import os

# Add agents path to import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

from bert_detection import bert_detect


def test_bert():
    """Unit test: Verify BERT classification works correctly"""
    
    print("\n" + "="*70)
    print("🧪 BERT CLASSIFICATION TEST")
    print("="*70)
    
    # Load sample logs
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_logs.csv')
    df = pd.read_csv(data_path)
    
    print(f"\n📊 Loaded {len(df)} logs from sample_logs.csv")
    
    # Run BERT detection
    print("🚀 Running bert_detect()...")
    result_df = bert_detect(df)
    
    # Verify new columns exist
    required_cols = ['bert_class', 'bert_confidence', 'severity']
    for col in required_cols:
        assert col in result_df.columns, f"❌ Missing column: {col}"
    
    print(f"✅ All required columns present: {required_cols}")
    
    # Show first 8 results
    print("\n📋 First 8 classified logs:")
    print("-" * 70)
    display_df = result_df[['ip', 'raw_message', 'bert_class', 'bert_confidence', 'severity']].head(8)
    for idx, row in display_df.iterrows():
        print(f"{row['ip']:15} | {row['bert_class']:12} | {row['bert_confidence']:.3f} | {row['severity']}")
    
    # Verify classification distribution
    print("\n📊 Classification Distribution:")
    print("-" * 70)
    class_counts = result_df['bert_class'].value_counts()
    for threat_class, count in class_counts.items():
        percentage = (count / len(result_df)) * 100
        print(f"  {threat_class:12}: {count:3} logs ({percentage:5.1f}%)")
    
    # Verify confidence scores
    print("\n📈 Confidence Score Statistics:")
    print("-" * 70)
    print(f"  Min confidence:  {result_df['bert_confidence'].min():.3f}")
    print(f"  Max confidence:  {result_df['bert_confidence'].max():.3f}")
    print(f"  Avg confidence:  {result_df['bert_confidence'].mean():.3f}")
    
    # Verify severity mapping
    print("\n🔴 Severity Distribution:")
    print("-" * 70)
    severity_counts = result_df['severity'].value_counts()
    for severity, count in severity_counts.items():
        percentage = (count / len(result_df)) * 100
        print(f"  {severity:10}: {count:3} logs ({percentage:5.1f}%)")
    
    # Final check
    assert len(result_df) == len(df), "❌ Row count mismatch"
    assert result_df['bert_class'].isnull().sum() == 0, "❌ Found null values in bert_class"
    assert result_df['bert_confidence'].isnull().sum() == 0, "❌ Found null values in bert_confidence"
    assert result_df['severity'].isnull().sum() == 0, "❌ Found null values in severity"
    
    print("\n" + "="*70)
    print("✅ PASSED - BERT classification successful!")
    print("="*70 + "\n")
    
    return result_df


if __name__ == "__main__":
    test_bert()
