"""
THREAT INTELLIGENCE ENRICHMENT MODEL
Uses BERT to predict TI profiles for incidents.
"""
import json
import os
import warnings

import pandas as pd
import torch
from transformers import BertForSequenceClassification, BertTokenizer

warnings.filterwarnings("ignore")

_BASE_PROFILES = {
    "brute_force": {
        "category": "Authentication Attack",
        "risk_level": "MEDIUM",
        "description": "Multiple failed login attempts indicating password guessing",
        "impact": "Account compromise, unauthorized access",
        "mitigation": "Enable MFA, implement account lockout, monitor failed logins",
    },
    "malware": {
        "category": "Malicious Software",
        "risk_level": "HIGH",
        "description": "Malware activity including trojans or malicious code",
        "impact": "System compromise, data theft",
        "mitigation": "Isolate host, run antivirus scan, analyze malware",
    },
    "phishing": {
        "category": "Social Engineering",
        "risk_level": "MEDIUM",
        "description": "Fraudulent communication to steal credentials",
        "impact": "Credential theft, account takeover",
        "mitigation": "Block URLs, user training, email filtering",
    },
    "ddos": {
        "category": "Denial of Service",
        "risk_level": "MEDIUM",
        "description": "Traffic flood to overwhelm services",
        "impact": "Service unavailability",
        "mitigation": "Enable DDoS protection, rate limiting",
    },
    "ransomware": {
        "category": "Extortion Malware",
        "risk_level": "HIGH",
        "description": "Malware encrypting files and demanding payment",
        "impact": "Data encryption and loss",
        "mitigation": "Isolate immediately, restore from backup",
    },
    "data_exfil": {
        "category": "Data Breach",
        "risk_level": "HIGH",
        "description": "Unauthorized data exfiltration",
        "impact": "Data loss and breach",
        "mitigation": "Block external connections",
    },
    "insider_threat": {
        "category": "Insider Activity",
        "risk_level": "HIGH",
        "description": "Suspicious insider activity",
        "impact": "Privilege abuse and theft",
        "mitigation": "Review permissions and disable account",
    },
    "normal": {
        "category": "Normal Activity",
        "risk_level": "LOW",
        "description": "Standard system or user activity",
        "impact": "No impact",
        "mitigation": "Continue monitoring",
    },
}

TI_PROFILES = {
    f"{threat}|{profile['risk_level']}": {
        "category": profile["category"],
        "risk_level": profile["risk_level"],
        "description": profile["description"],
        "impact": profile["impact"],
        "mitigation": profile["mitigation"],
    }
    for threat, profile in _BASE_PROFILES.items()
}


class TIEnrichmentBERTModel:
    def __init__(self, model_path="models/ti_enrichment_bert"):
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        config_file = os.path.join(model_path, "config.json")
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Model config not found at {config_file}. "
                "Please train the model first using train_ti_enrichment_bert_model.py"
            )

        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.id_to_label = {int(k): v for k, v in self.config["id_to_label"].items()}
        self.max_length = self.config["max_length"]

        self.tokenizer = BertTokenizer.from_pretrained(model_path)
        self.model = BertForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()

    def predict(self, texts, batch_size=32):
        labels = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            inputs = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model(**inputs)
                preds = torch.argmax(outputs.logits, dim=-1).cpu().numpy()
            labels.extend([self.id_to_label[int(pred)] for pred in preds])
        return labels


_global_ti_model = None


def _build_incident_text(row):
    return (
        f"Incident type: {row['threat_type']}. "
        f"Severity: {row.get('severity', 'MEDIUM')}. "
        f"Alert count: {row.get('alert_count', 1)}."
    )


def enrich_with_threat_intel(incidents_df, model_path="models/ti_enrichment_bert", batch_size=32):
    if incidents_df is None or len(incidents_df) == 0:
        print("No incidents to enrich")
        return pd.DataFrame()

    global _global_ti_model
    if _global_ti_model is None:
        _global_ti_model = TIEnrichmentBERTModel(model_path)

    enriched = incidents_df.copy()
    texts = enriched.apply(_build_incident_text, axis=1).tolist()
    labels = _global_ti_model.predict(texts, batch_size=batch_size)

    profiles = []
    for label in labels:
        profiles.append(TI_PROFILES.get(label, {
            "category": "Unknown",
            "risk_level": "UNKNOWN",
            "description": "No profile available",
            "impact": "Unknown",
            "mitigation": "Investigate further",
        }))

    enriched["ti_label"] = labels
    enriched["ti_category"] = [p["category"] for p in profiles]
    enriched["ti_risk_level"] = [p["risk_level"] for p in profiles]
    enriched["ti_description"] = [p["description"] for p in profiles]
    enriched["ti_impact"] = [p["impact"] for p in profiles]
    enriched["ti_mitigation"] = [p["mitigation"] for p in profiles]

    return enriched


def get_threat_details(label):
    return TI_PROFILES.get(label, {
        "category": "Unknown",
        "risk_level": "UNKNOWN",
        "description": "No threat intelligence available",
        "impact": "Unknown",
        "mitigation": "Manual investigation required",
    })


def print_enriched_report(enriched_df):
    if len(enriched_df) == 0:
        print("No enriched incidents to display")
        return

    print("\n" + "=" * 100)
    print("THREAT INTELLIGENCE ENRICHED INCIDENT REPORT")
    print("=" * 100)

    for idx, incident in enriched_df.iterrows():
        print("\n" + "-" * 100)
        print(f"INCIDENT #{idx + 1}")
        print("-" * 100)
        print(f"Source IP:        {incident.get('source_ip', 'N/A')}")
        print(f"Time Window:      {incident.get('time_window', 'N/A')}")
        print(f"Threat Type:      {incident['threat_type']}")
        print(f"Alert Count:      {incident.get('alert_count', 'N/A')}")
        print(f"Avg Confidence:   {incident.get('avg_confidence', 0):.3f}")
        print(f"Severity:         {incident.get('severity', 'N/A')}")

        print("\nTHREAT INTELLIGENCE:")
        print(f"  Category:       {incident['ti_category']}")
        print(f"  Risk Level:     {incident['ti_risk_level']}")
        print(f"  Description:    {incident['ti_description']}")
        print(f"  Impact:         {incident['ti_impact']}")
        print(f"  Mitigation:     {incident['ti_mitigation']}")

    print("\n" + "=" * 100)
    print(f"Total enriched incidents: {len(enriched_df)}")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    sample_incidents = pd.DataFrame(
        {
            "source_ip": ["192.168.1.100", "10.0.0.50"],
            "time_window": ["2026-01-05 10:00:00", "2026-01-05 10:05:00"],
            "threat_type": ["brute_force", "malware"],
            "alert_count": [25, 5],
            "avg_confidence": [0.998, 0.995],
            "severity": ["MEDIUM", "HIGH"],
            "users": [["admin", "root"], ["john"]],
        }
    )

    enriched = enrich_with_threat_intel(sample_incidents)
    print_enriched_report(enriched)
