"""
Test script to debug the upload issue
"""
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.bert_detection import bert_detect

# Read test CSV
print("📁 Reading data/realistic_logs.csv...")
df = pd.read_csv('data/realistic_logs.csv', encoding='utf-8')
print(f"✅ Loaded {len(df)} rows")
print(f"📋 Columns: {df.columns.tolist()}")

# Test BERT detection
print("\n🔍 Running BERT detection...")
try:
    result_df = bert_detect(df)
    print(f"✅ BERT detection successful!")
    print(f"📊 Added columns: {[col for col in result_df.columns if col not in df.columns]}")
    print(f"\n📋 Sample results:")
    print(result_df[['raw_message', 'bert_class', 'bert_confidence', 'severity']].head())
    
    # Check for incidents
    incidents = result_df[result_df['bert_class'] != 'normal']
    print(f"\n🚨 Found {len(incidents)} incidents (non-normal)")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
