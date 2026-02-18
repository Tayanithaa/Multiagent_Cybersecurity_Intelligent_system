#!/bin/bash
#
# Model Training Script
# Trains BERT model on new malware analysis results
#

set -e

PROJECT_DIR="/home/deepak/Desktop/Multiagent_Cybersecurity_Intelligent_system"
cd "$PROJECT_DIR"

echo "=========================================="
echo "BERT Model Training Pipeline"
echo "=========================================="
echo ""

source venv/bin/activate

# Menu
echo "Select training option:"
echo ""
echo "1. Quick Training (5 epochs, ~10 minutes)"
echo "2. Full Training (15 epochs, ~30 minutes)"
echo "3. Generate synthetic data first, then train"
echo "4. Use EMBER dataset"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "🔄 Starting quick training (5 epochs)..."
        python train_bert_model.py \
            --epochs 5 \
            --learning_rate 2e-5 \
            --batch_size 32 \
            --warmup_steps 500 \
            --weight_decay 0.01
        ;;
    2)
        echo "🔄 Starting full training (15 epochs)..."
        python train_bert_model.py \
            --epochs 15 \
            --learning_rate 2e-5 \
            --batch_size 32 \
            --warmup_steps 500 \
            --weight_decay 0.01 \
            --max_length 512
        ;;
    3)
        echo "🔄 Generating synthetic training data..."
        python generate_realistic_logs.py --count 2000
        
        echo "Converting to training format..."
        python data/converter.py
        
        echo "Training model..."
        python train_bert_model.py \
            --epochs 10 \
            --learning_rate 2e-5 \
            --batch_size 32
        ;;
    4)
        echo "Checking for EMBER dataset..."
        if [ ! -f "data/EMBER.json" ]; then
            echo "EMBER dataset not found. Downloading..."
            cd data
            kaggle datasets download -d unicamp-dl/malware-research-ember
            unzip -o malware-research-ember.zip
            cd ..
        fi
        
        echo "Converting EMBER to training format..."
        python data/converter.py --format ember
        
        echo "Training model on EMBER..."
        python train_bert_model.py \
            --epochs 20 \
            --learning_rate 2e-5 \
            --batch_size 32 \
            --dataset ember
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "✅ Training Complete!"
echo "=========================================="
echo ""
echo "Model saved to: models/distilbert_log_classifier/"
echo ""
echo "Next steps:"
echo "1. Restart backend API to load new model"
echo "2. Test with new malware samples"
echo "3. Check improved detection accuracy"
echo ""

# Show model stats
echo "Model Information:"
ls -lh models/distilbert_log_classifier/model.safetensors

echo ""
read -p "Do you want to restart the backend API? (y/n): " confirm
if [ "$confirm" = "y" ]; then
    echo "Attempting to restart backend..."
    pkill -f "uvicorn" || true
    sleep 2
    python -m uvicorn backend.main:app --reload --port 8000 &
    echo "Backend restarted at http://localhost:8000"
fi
