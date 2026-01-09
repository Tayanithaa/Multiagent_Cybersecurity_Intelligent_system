"""
PRODUCTION BERT DETECTION MODULE
Replaces the toy TF-IDF classifier with trained DistilBERT model
"""
import pandas as pd
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import json
import os
import warnings
warnings.filterwarnings('ignore')


class BERTLogClassifier:
    """Production BERT-based log classifier using fine-tuned DistilBERT"""
    
    def __init__(self, model_path="models/distilbert_log_classifier"):
        """
        Initialize the classifier with trained model
        
        Args:
            model_path: Path to saved DistilBERT model directory
        """
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load config
        config_file = os.path.join(model_path, "config.json")
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Model config not found at {config_file}. "
                "Please train the model first using train_bert_model.py"
            )
        
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.label_map = self.config["label_map"]
        self.id_to_label = {int(k): v for k, v in self.config["id_to_label"].items()}
        self.max_length = self.config["max_length"]
        self.num_labels = len(self.label_map)
        
        # Load model and tokenizer
        print(f"Loading model from {model_path}...")
        print(f"Model has {self.num_labels} classes: {list(self.label_map.keys())}")
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_path)
        self.model = DistilBertForSequenceClassification.from_pretrained(
            model_path,
            num_labels=self.num_labels
        )
        self.model.to(self.device)
        self.model.eval()
        print(f"✅ Model loaded on {self.device}")
    
    def _classify_batch(self, messages):
        """
        Classify a batch of messages
        
        Args:
            messages: List of raw log messages
            
        Returns:
            List of tuples (class_name, confidence)
        """
        # Tokenize
        inputs = self.tokenizer(
            messages,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
        
        # Get predictions
        predictions = torch.argmax(probs, dim=-1).cpu().numpy()
        confidences = torch.max(probs, dim=-1).values.cpu().numpy()
        
        results = []
        for pred_id, conf in zip(predictions, confidences):
            class_name = self.id_to_label[pred_id]
            results.append((class_name, float(conf)))
        
        return results
    
    def _get_severity(self, bert_class, confidence):
        """
        Map classification to severity level
        
        Args:
            bert_class: Predicted threat class
            confidence: Prediction confidence (0-1)
            
        Returns:
            Severity level: HIGH/MEDIUM/LOW
        """
        # High-risk threats
        high_risk = ["ransomware", "malware", "data_exfil", "insider_threat"]
        # Medium-risk threats
        medium_risk = ["brute_force", "phishing", "ddos"]
        
        if bert_class in high_risk:
            return "HIGH" if confidence > 0.7 else "MEDIUM"
        elif bert_class in medium_risk:
            return "MEDIUM" if confidence > 0.7 else "LOW"
        else:  # normal
            return "LOW"
    
    def detect(self, df, batch_size=32):
        """
        Classify logs using trained DistilBERT model
        
        Input: DataFrame with columns [timestamp, user, ip, event_type, status, raw_message]
        Output: Same DataFrame + 3 new columns [bert_class, bert_confidence, severity]
        
        Args:
            df: Input DataFrame with raw_message column
            batch_size: Batch size for inference
            
        Returns:
            DataFrame with added classification columns
        """
        df = df.copy()
        
        # Support both 'message' and 'raw_message' column names
        if 'message' in df.columns:
            messages = df['message'].tolist()
        elif 'raw_message' in df.columns:
            messages = df['raw_message'].tolist()
        else:
            raise ValueError("DataFrame must have either 'message' or 'raw_message' column")
        
        # Process in batches
        all_classifications = []
        all_confidences = []
        all_severities = []
        
        for i in range(0, len(messages), batch_size):
            batch_messages = messages[i:i+batch_size]
            results = self._classify_batch(batch_messages)
            
            for class_name, confidence in results:
                severity = self._get_severity(class_name, confidence)
                all_classifications.append(class_name)
                all_confidences.append(confidence)
                all_severities.append(severity)
        
        # Add new columns
        df['bert_class'] = all_classifications
        df['bert_confidence'] = all_confidences
        df['severity'] = all_severities
        
        return df


# ==============================================================================
# PUBLIC INTERFACE (compatible with existing code)
# ==============================================================================
_global_detector = None

def bert_detect(df, model_path="models/distilbert_log_classifier"):
    """
    Public function to run BERT detection (drop-in replacement)
    
    Args:
        df: DataFrame with raw_message column
        model_path: Path to trained model (default: models/distilbert_log_classifier)
        
    Returns:
        DataFrame with bert_class, bert_confidence, severity columns
    """
    global _global_detector
    
    # Lazy load model (only once)
    if _global_detector is None:
        _global_detector = BERTLogClassifier(model_path)
    
    return _global_detector.detect(df)


# ==============================================================================
# STANDALONE TESTING
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING BERT LOG CLASSIFIER")
    print("="*80)
    
    # Test with sample logs
    test_data = pd.DataFrame({
        "timestamp": ["2026-01-03 10:00:00"] * 8,
        "user": ["alice"] * 8,
        "ip": ["192.168.1.100"] * 8,
        "raw_message": [
            "User logged in successfully",
            "Multiple failed login attempts detected",
            "Suspicious executable detected in temp directory",
            "Email contains malicious link asking for credentials",
            "High volume of requests detected from single IP",
            "Multiple files encrypted in short time interval",
            "Large outbound data transfer to external server",
            "Admin accessed confidential files outside business hours"
        ]
    })
    
    print("\n📋 Input logs:")
    for idx, msg in enumerate(test_data['raw_message'], 1):
        print(f"  {idx}. {msg}")
    
    print("\n🚀 Running classification...")
    results = bert_detect(test_data)
    
    print("\n📊 Results:")
    print("-" * 80)
    for idx, row in results.iterrows():
        print(f"{idx+1}. {row['bert_class']:15} | Conf: {row['bert_confidence']:.3f} | {row['severity']:6} | {row['raw_message'][:50]}")
    
    print("\n✅ Test complete!")
