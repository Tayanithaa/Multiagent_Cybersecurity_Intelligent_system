# 🚀 DistilBERT Training Pipeline - 10 Hour Sprint

## 📋 Overview
Transform the toy classifier into a production-grade DistilBERT model for security log classification.

**Goal:** Train a real transformer model on 8 threat classes with 90%+ precision.

---

## ⏱️ Timeline (10 hours)

### **Hour 0-1: Setup & Data Generation**
```powershell
# 1. Install dependencies
.\venv\Scripts\Activate.ps1
pip install torch transformers datasets accelerate --upgrade

# 2. Generate 8,000 labeled logs (1,000 per class)
python data/generate_training_data.py
```

**Output:** `data/training/full_dataset.csv` with 8,000 labeled samples

---

### **Hour 1-3: Prepare Training Environment**

**Check GPU:**
```python
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.get_device_name(0))  # Your GPU name
```

**Verify dataset:**
```powershell
python -c "import pandas as pd; df = pd.read_csv('data/training/full_dataset.csv'); print(df['label'].value_counts())"
```

---

### **Hour 3-7: Model Training (GPU)**

```powershell
# Train DistilBERT (this takes 2-4 hours on GPU)
python train_bert_model.py
```

**What happens:**
- Downloads DistilBERT (66M parameters)
- Splits data: 72% train / 8% val / 20% test
- Fine-tunes for 5 epochs with early stopping
- Saves best model to `models/distilbert_log_classifier/`

**Expected output:**
```
🖥️  Using device: cuda
GPU: NVIDIA GeForce RTX 3060
Memory: 12.00 GB

📂 Loading dataset...
✅ Loaded 8000 samples

🔪 Splitting dataset...
  Train: 5760 samples
  Val:   576 samples
  Test:  1600 samples

🚀 Starting training...
Epoch 1/5: [████████████] loss: 0.452
Epoch 2/5: [████████████] loss: 0.234
...
✅ Training complete!
⏱️  Training time: 156.23 minutes

📊 Test precision: 0.9412
📊 Test F1: 0.9385
```

---

### **Hour 7-8: Model Integration**

Replace old classifier:
```powershell
# Backup old version
mv agents\bert_detection.py agents\bert_detection_OLD.py

# Use new BERT model
mv agents\bert_detection_new.py agents\bert_detection.py
```

**Test inference:**
```powershell
python agents\bert_detection.py
```

---

### **Hour 8-9: End-to-End Testing**

```powershell
# Test full pipeline
python tests\test_correlation.py
```

**Expected behavior:**
- BERT model loads from `models/distilbert_log_classifier/`
- Classifies logs with 90%+ confidence
- Correlation groups alerts into incidents
- Shows HIGH severity for ransomware/malware

---

### **Hour 9-10: Documentation & Validation**

**Create results report:**
```powershell
# View training metrics
cat models\distilbert_log_classifier\evaluation_results.json
```

**Test on real scenarios:**
```python
import pandas as pd
from agents.bert_detection import bert_detect

# Test brute force
brute_force_logs = pd.read_csv("data/brute_force.csv")
results = bert_detect(brute_force_logs)
print(results[['raw_message', 'bert_class', 'bert_confidence', 'severity']].head())
```

---

## 🎯 Success Criteria

✅ **Model trained** - `models/distilbert_log_classifier/` exists  
✅ **Precision > 90%** - Check `evaluation_results.json`  
✅ **GPU used** - Training < 4 hours  
✅ **8 classes** - normal, brute_force, malware, phishing, ddos, ransomware, data_exfil, insider_threat  
✅ **Tests pass** - `test_correlation.py` runs without errors  
✅ **Inference works** - New logs classified correctly  

---

## 📊 Configuration Tuning

**If training is too slow (>4 hours):**
```python
# In train_bert_model.py, reduce:
"batch_size": 32,  # Increase if you have RAM
"num_epochs": 3,   # Reduce epochs
```

**If accuracy is low (<85%):**
```python
# In generate_training_data.py:
SAMPLES_PER_CLASS = 2000  # More data

# In train_bert_model.py:
"num_epochs": 8,          # More epochs
"learning_rate": 1e-5,    # Lower learning rate
```

**If GPU out of memory:**
```python
"batch_size": 8,          # Reduce batch size
"max_length": 64,         # Reduce sequence length
```

---

## 🐛 Troubleshooting

**Error: "CUDA out of memory"**
```python
# Reduce batch size in train_bert_model.py
"batch_size": 8,
```

**Error: "Model not found"**
```powershell
# Make sure training completed
ls models\distilbert_log_classifier\
# Should show: config.json, pytorch_model.bin, tokenizer files
```

**Slow training:**
```python
# Verify GPU is used
import torch
print(torch.cuda.is_available())  # Must be True
```

---

## 📈 Expected Performance

| Metric | Target | Typical |
|--------|--------|---------|
| Training time (GPU) | < 4 hours | 2.5 hours |
| Test Precision | > 90% | 94% |
| Test F1 | > 88% | 93% |
| Inference speed | < 100ms/log | 30ms |
| Model size | < 500MB | 268MB |

---

## 🔥 Quick Start (Copy-Paste)

```powershell
# Complete pipeline in 4 commands:
.\venv\Scripts\Activate.ps1
pip install torch transformers datasets accelerate
python data/generate_training_data.py
python train_bert_model.py

# After training completes:
mv agents\bert_detection.py agents\bert_detection_OLD.py
mv agents\bert_detection_new.py agents\bert_detection.py
python tests\test_correlation.py
```

---

## 📚 What You'll Learn

1. **Data preparation** - Generating balanced labeled datasets
2. **Train/val/test splits** - Proper ML evaluation
3. **Transformer fine-tuning** - Using Hugging Face transformers
4. **GPU acceleration** - PyTorch CUDA
5. **Model persistence** - Saving and loading models
6. **Evaluation metrics** - Precision, recall, F1, confusion matrix
7. **Batch inference** - Efficient prediction on large datasets
8. **Production deployment** - Drop-in replacement for existing code

---

## ✅ Checklist

- [ ] GPU available and working
- [ ] Dependencies installed
- [ ] 8,000 training samples generated
- [ ] Model training started
- [ ] Training completed (2-4 hours)
- [ ] Test precision > 90%
- [ ] Model saved successfully
- [ ] Old bert_detection.py backed up
- [ ] New model integrated
- [ ] End-to-end test passes
- [ ] Documentation complete

---

**Ready? Start with Step 1: Generate training data!**

```powershell
python data/generate_training_data.py
```
