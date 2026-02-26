"""
Train ALBERT model for response recommendation.
"""
import json
from datetime import datetime

import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from transformers import (
    AlbertForSequenceClassification,
    AlbertTokenizer,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)


CONFIG = {
    "data_path": "data/training/csv/response/response_agent_training.csv",
    "model_name": "albert-base-v2",
    "output_dir": "models/response_albert",
    "max_length": 128,
    "batch_size": 16,
    "learning_rate": 2e-5,
    "num_epochs": 4,
    "warmup_steps": 200,
    "weight_decay": 0.01,
    "test_size": 0.2,
    "val_size": 0.1,
    "random_state": 42,
}


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="weighted"
    )
    return {"precision": precision, "recall": recall, "f1": f1}


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    df = pd.read_csv(CONFIG["data_path"])
    required_cols = {"threat_type", "severity", "confidence", "alert_count", "recommended_action"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError("Dataset missing required response columns")

    df["text"] = (
        "threat_type="
        + df["threat_type"].astype(str)
        + "; severity="
        + df["severity"].astype(str)
        + "; confidence="
        + df["confidence"].astype(str)
        + "; alert_count="
        + df["alert_count"].astype(str)
    )

    unique_labels = sorted(df["recommended_action"].unique())
    label_map = {label: idx for idx, label in enumerate(unique_labels)}
    id_to_label = {idx: label for label, idx in label_map.items()}
    df["label_id"] = df["recommended_action"].map(label_map)

    train_val_df, test_df = train_test_split(
        df,
        test_size=CONFIG["test_size"],
        random_state=CONFIG["random_state"],
        stratify=df["label_id"],
    )

    train_df, val_df = train_test_split(
        train_val_df,
        test_size=CONFIG["val_size"],
        random_state=CONFIG["random_state"],
        stratify=train_val_df["label_id"],
    )

    tokenizer = AlbertTokenizer.from_pretrained(CONFIG["model_name"])

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            padding="max_length",
            truncation=True,
            max_length=CONFIG["max_length"],
        )

    train_dataset = Dataset.from_dict(
        {"text": train_df["text"].tolist(), "label": train_df["label_id"].tolist()}
    )
    val_dataset = Dataset.from_dict(
        {"text": val_df["text"].tolist(), "label": val_df["label_id"].tolist()}
    )
    test_dataset = Dataset.from_dict(
        {"text": test_df["text"].tolist(), "label": test_df["label_id"].tolist()}
    )

    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)
    test_dataset = test_dataset.map(tokenize_function, batched=True)

    model = AlbertForSequenceClassification.from_pretrained(
        CONFIG["model_name"], num_labels=len(label_map)
    )

    training_args = TrainingArguments(
        output_dir=CONFIG["output_dir"],
        evaluation_strategy="epoch",
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
        report_to="none",
        fp16=torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    print("Starting training...")
    start_time = datetime.now()
    trainer.train()
    training_time = (datetime.now() - start_time).total_seconds()

    model.config.num_labels = len(label_map)
    model.config.id2label = {i: label for label, i in label_map.items()}
    model.config.label2id = label_map

    model.save_pretrained(CONFIG["output_dir"])
    tokenizer.save_pretrained(CONFIG["output_dir"])

    config_data = {
        "label_map": label_map,
        "id_to_label": id_to_label,
        "max_length": CONFIG["max_length"],
        "model_name": CONFIG["model_name"],
        "training_samples": len(train_df),
        "training_time_minutes": training_time / 60,
        "timestamp": datetime.now().isoformat(),
    }

    with open(f"{CONFIG['output_dir']}/config.json", "w") as f:
        json.dump(config_data, f, indent=2)

    print("Evaluating on test set...")
    test_results = trainer.predict(test_dataset)
    predictions = np.argmax(test_results.predictions, axis=1)
    true_labels = test_results.label_ids

    print("CLASSIFICATION REPORT (Test Set)")
    print(classification_report(true_labels, predictions, digits=4))

    cm = confusion_matrix(true_labels, predictions)
    eval_results = {
        "test_metrics": test_results.metrics,
        "classification_report": classification_report(
            true_labels, predictions, output_dict=True
        ),
        "confusion_matrix": cm.tolist(),
    }

    with open(f"{CONFIG['output_dir']}/evaluation_results.json", "w") as f:
        json.dump(eval_results, f, indent=2)

    print("Training complete")


+if __name__ == "__main__":
+    main()
