"""
QUICK START: Complete Training Pipeline in One Command
Run this after dependencies are installed
"""
import subprocess
import sys
import os

def run_command(description, command):
    """Run a command and track progress"""
    print(f"\n{'='*80}")
    print(f"🚀 {description}")
    print(f"{'='*80}")
    
    result = subprocess.run(
        command,
        shell=True,
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"❌ Error in: {description}")
        sys.exit(1)
    
    print(f"✅ Completed: {description}")
    return result

def main():
    print("\n" + "="*80)
    print("🎯 DISTILBERT TRAINING PIPELINE - 10 HOUR SPRINT")
    print("="*80)
    
    # Step 1: Generate training data
    run_command(
        "Step 1/4: Generate 8,000 labeled training samples",
        "python data/training/scripts/generate_training_data.py"
    )
    
    # Step 2: Train model
    run_command(
        "Step 2/4: Train DistilBERT model (2-4 hours on GPU)",
        "python training/train_bert_model.py"
    )
    
    # Step 3: Test BERT model
    run_command(
        "Step 3/4: Test BERT model",
        "python agents/bert_detection.py"
    )
    
    run_command(
        "Step 4/4: End-to-end pipeline test",
        "python tests/test_correlation.py"
    )
    
    print("\n" + "="*80)
    print("✅ TRAINING PIPELINE COMPLETE!")
    print("="*80)
    print(f"\n📊 Model saved to: models/distilbert_log_classifier/")
    print(f"📈 View results: models/distilbert_log_classifier/evaluation_results.json")
    print(f"🎯 Ready for production!")

if __name__ == "__main__":
    main()
