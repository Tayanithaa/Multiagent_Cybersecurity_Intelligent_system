"""
STEP 2: Train DistilBERT Model for Log Classification
This script fine-tunes DistilBERT on security logs with proper train/val/test split
"""
import pandas as pd
import numpy as np
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback
)
from datasets import Dataset
import os
import json
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CONFIG = {
    "data_path": "data/training/full_dataset.csv",
    "model_name": "distilbert-base-uncased",
    "output_dir": "models/distilbert_log_classifier",
    "max_length": 128,
    "batch_size": 16,
    "learning_rate": 2e-5,
    "num_epochs": 5,
    "warmup_steps": 500,
    "weight_decay": 0.01,
    "test_size": 0.2,
    "val_size": 0.1,
    "random_state": 42,
}

# Class labels
LABEL_MAP = {
    "normal": 0,
    "brute_force": 1,
    "malware": 2,
    "phishing": 3,
    "ddos": 4,
    "ransomware": 5,
    "data_exfil": 6,
    "insider_threat": 7
}

ID_TO_LABEL = {v: k for k, v in LABEL_MAP.items()}

# ==============================================================================
# CHECK GPU
# ==============================================================================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"\n🖥️  Using device: {device}")
if device == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB\n")

# ==============================================================================
# LOAD DATA
# ==============================================================================
print("📂 Loading dataset...")
df = pd.read_csv(CONFIG["data_path"])
print(f"✅ Loaded {len(df)} samples")
print(f"\n📊 Class distribution:")
print(df['label'].value_counts())

# ==============================================================================
# TRAIN/VAL/TEST SPLIT
# ==============================================================================
print("\n🔪 Splitting dataset...")

# First split: train+val vs test
train_val_df, test_df = train_test_split(
    df, 
    test_size=CONFIG["test_size"], 
    random_state=CONFIG["random_state"],
    stratify=df['label_id']
)

# Second split: train vs val
train_df, val_df = train_test_split(
    train_val_df,
    test_size=CONFIG["val_size"],
    random_state=CONFIG["random_state"],
    stratify=train_val_df['label_id']
)

print(f"  Train: {len(train_df)} samples")
print(f"  Val:   {len(val_df)} samples")
print(f"  Test:  {len(test_df)} samples")

# ==============================================================================
# TOKENIZATION
# ==============================================================================
print("\n🔤 Loading tokenizer...")
tokenizer = DistilBertTokenizer.from_pretrained(CONFIG["model_name"])

def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=CONFIG["max_length"]
    )

# Prepare datasets
print("🔤 Tokenizing datasets...")
train_dataset = Dataset.from_dict({
    "text": train_df["raw_message"].tolist(),
    "label": train_df["label_id"].tolist()
})

val_dataset = Dataset.from_dict({
    "text": val_df["raw_message"].tolist(),
    "label": val_df["label_id"].tolist()
})

test_dataset = Dataset.from_dict({
    "text": test_df["raw_message"].tolist(),
    "label": test_df["label_id"].tolist()
})

train_dataset = train_dataset.map(tokenize_function, batched=True)
val_dataset = val_dataset.map(tokenize_function, batched=True)
test_dataset = test_dataset.map(tokenize_function, batched=True)

print("✅ Tokenization complete")

# ==============================================================================
# MODEL
# ==============================================================================
print(f"\n🤖 Loading DistilBERT model...")
model = DistilBertForSequenceClassification.from_pretrained(
    CONFIG["model_name"],
    num_labels=len(LABEL_MAP)
)
print("✅ Model loaded")

# ==============================================================================
# TRAINING ARGUMENTS
# ==============================================================================
training_args = TrainingArguments(
    output_dir=CONFIG["output_dir"],
    eval_strategy="epoch",  # Changed from evaluation_strategy
    save_strategy="epoch",
    learning_rate=CONFIG["learning_rate"],
    per_device_train_batch_size=CONFIG["batch_size"],
    per_device_eval_batch_size=CONFIG["batch_size"],
    num_train_epochs=CONFIG["num_epochs"],
    weight_decay=CONFIG["weight_decay"],
    warmup_steps=CONFIG["warmup_steps"],
    logging_dir=f"{CONFIG['output_dir']}/logs",
    logging_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    save_total_limit=2,
    report_to="none",  # Disable wandb/tensorboard for now
    fp16=torch.cuda.is_available(),  # Mixed precision if GPU available
)

# ==============================================================================
# METRICS
# ==============================================================================
def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='weighted'
    )
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

# ==============================================================================
# TRAINER
# ==============================================================================
print("\n🏋️  Initializing trainer...")
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    #tokenizer=tokenizer,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
)

# ==============================================================================
# TRAINING
# ==============================================================================
print("\n🚀 Starting training...")
print(f"📊 Epochs: {CONFIG['num_epochs']}")
print(f"📊 Batch size: {CONFIG['batch_size']}")
print(f"📊 Learning rate: {CONFIG['learning_rate']}")
print("="*80)

start_time = datetime.now()
trainer.train()
training_time = (datetime.now() - start_time).total_seconds()

print("\n✅ Training complete!")
print(f"⏱️  Training time: {training_time/60:.2f} minutes")

# ==============================================================================
# SAVE MODEL
# ==============================================================================
print("\n💾 Saving model...")

# Update model config with correct num_labels and label mappings
model.config.num_labels = len(LABEL_MAP)
model.config.id2label = {i: label for label, i in LABEL_MAP.items()}
model.config.label2id = LABEL_MAP

model.save_pretrained(CONFIG["output_dir"])
tokenizer.save_pretrained(CONFIG["output_dir"])

# Save config and label map
config_data = {
    "label_map": LABEL_MAP,
    "id_to_label": ID_TO_LABEL,
    "max_length": CONFIG["max_length"],
    "model_name": CONFIG["model_name"],
    "training_samples": len(train_df),
    "training_time_minutes": training_time/60,
    "timestamp": datetime.now().isoformat()
}

with open(f"{CONFIG['output_dir']}/config.json", "w") as f:
    json.dump(config_data, f, indent=2)

print(f"✅ Model saved to: {CONFIG['output_dir']}")

# ==============================================================================
# EVALUATION ON TEST SET
# ==============================================================================
print("\n📊 Evaluating on test set...")
test_results = trainer.predict(test_dataset)

predictions = np.argmax(test_results.predictions, axis=1)
true_labels = test_results.label_ids

# Classification report
print("\n" + "="*80)
print("CLASSIFICATION REPORT (Test Set)")
print("="*80)
print(classification_report(
    true_labels,
    predictions,
    target_names=list(LABEL_MAP.keys()),
    digits=4
))

# Confusion matrix
print("\n" + "="*80)
print("CONFUSION MATRIX")
print("="*80)
cm = confusion_matrix(true_labels, predictions)
print(cm)

# Save evaluation results
eval_results = {
    "test_metrics": test_results.metrics,
    "classification_report": classification_report(
        true_labels,
        predictions,
        target_names=list(LABEL_MAP.keys()),
        output_dict=True
    ),
    "confusion_matrix": cm.tolist()
}

with open(f"{CONFIG['output_dir']}/evaluation_results.json", "w") as f:
    json.dump(eval_results, f, indent=2)

print(f"\n✅ Evaluation results saved to: {CONFIG['output_dir']}/evaluation_results.json")

# ==============================================================================
# SUMMARY
# ==============================================================================
print("\n" + "="*80)
print("TRAINING SUMMARY")
print("="*80)
print(f"Model: DistilBERT")
print(f"Training samples: {len(train_df)}")
print(f"Validation samples: {len(val_df)}")
print(f"Test samples: {len(test_df)}")
print(f"Training time: {training_time/60:.2f} minutes")
print(f"Test precision: {eval_results['classification_report']['weighted avg']['precision']:.4f}")
print(f"Test recall: {eval_results['classification_report']['weighted avg']['recall']:.4f}")
print(f"Test F1: {eval_results['classification_report']['weighted avg']['f1-score']:.4f}")
print(f"Model saved: {CONFIG['output_dir']}")
print("="*80)
print("\n✅ ALL DONE! Run the inference module to use the trained model.")
