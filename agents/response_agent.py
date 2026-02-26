"""
RESPONSE RECOMMENDATION MODEL
Uses ALBERT to predict primary response actions.
"""
import json
import os
import warnings

import pandas as pd
import torch
from transformers import AlbertForSequenceClassification, AlbertTokenizer

warnings.filterwarnings("ignore")

ACTIONS = {
    "BLOCK_IP": {
        "priority": 1,
        "description": "Block source IP address at firewall",
        "automation": "Can be automated",
        "tools": "Firewall, IPS, WAF",
    },
    "ISOLATE_HOST": {
        "priority": 1,
        "description": "Quarantine infected host from network",
        "automation": "Can be automated",
        "tools": "NAC, EDR, Network segmentation",
    },
    "ESCALATE": {
        "priority": 2,
        "description": "Escalate to senior SOC analyst or incident response team",
        "automation": "Semi-automated (alert)",
        "tools": "SOAR, Ticketing system, PagerDuty",
    },
    "RESET_PASSWORD": {
        "priority": 2,
        "description": "Force password reset for affected accounts",
        "automation": "Can be automated",
        "tools": "Active Directory, IAM",
    },
    "DISABLE_ACCOUNT": {
        "priority": 1,
        "description": "Disable compromised user accounts",
        "automation": "Can be automated",
        "tools": "Active Directory, IAM",
    },
    "MONITOR": {
        "priority": 3,
        "description": "Continue monitoring - no immediate action required",
        "automation": "Automated",
        "tools": "SIEM, Log monitoring",
    },
    "SCAN_SYSTEM": {
        "priority": 2,
        "description": "Run full antivirus/EDR scan on affected systems",
        "automation": "Can be automated",
        "tools": "Antivirus, EDR platform",
    },
    "BLOCK_URL": {
        "priority": 2,
        "description": "Block malicious URLs/domains",
        "automation": "Can be automated",
        "tools": "Web proxy, DNS filtering",
    },
    "RESTORE_BACKUP": {
        "priority": 1,
        "description": "Restore systems from clean backup",
        "automation": "Manual",
        "tools": "Backup system, Recovery tools",
    },
    "NOTIFY_LEGAL": {
        "priority": 1,
        "description": "Notify legal/compliance team for data breach",
        "automation": "Manual",
        "tools": "Email, Incident management",
    },
}


class ResponseAlbertModel:
    def __init__(self, model_path="models/response_albert"):
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        config_file = os.path.join(model_path, "config.json")
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Model config not found at {config_file}. "
                "Please train the model first using train_response_albert_model.py"
            )

        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.id_to_label = {int(k): v for k, v in self.config["id_to_label"].items()}
        self.max_length = self.config["max_length"]

        self.tokenizer = AlbertTokenizer.from_pretrained(model_path)
        self.model = AlbertForSequenceClassification.from_pretrained(model_path)
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


_global_response_model = None


def _build_action_text(row):
    return (
        f"threat_type={row['threat_type']}; "
        f"severity={row.get('severity', 'MEDIUM')}; "
        f"confidence={row.get('avg_confidence', 0.0):.3f}; "
        f"alert_count={row.get('alert_count', 1)}; "
        f"risk={row.get('ti_risk_level', 'UNKNOWN')}"
    )


def recommend_response(enriched_df, model_path="models/response_albert", batch_size=32):
    if enriched_df is None or len(enriched_df) == 0:
        print("No incidents to process")
        return pd.DataFrame()

    global _global_response_model
    if _global_response_model is None:
        _global_response_model = ResponseAlbertModel(model_path)

    response_df = enriched_df.copy()
    texts = response_df.apply(_build_action_text, axis=1).tolist()
    actions = _global_response_model.predict(texts, batch_size=batch_size)

    response_df["primary_action"] = actions
    response_df["secondary_action"] = ""

    response_df["action_priority"] = response_df["primary_action"].apply(
        lambda x: ACTIONS.get(x, {}).get("priority", 3)
    )
    response_df["automation_status"] = response_df["primary_action"].apply(
        lambda x: ACTIONS.get(x, {}).get("automation", "Unknown")
    )
    response_df["action_description"] = response_df["primary_action"].apply(
        lambda x: ACTIONS.get(x, {}).get("description", "No description")
    )

    response_df = response_df.sort_values("action_priority")
    return response_df


def get_action_details(action_name):
    return ACTIONS.get(
        action_name,
        {
            "priority": 3,
            "description": "Unknown action",
            "automation": "Unknown",
            "tools": "Unknown",
        },
    )


def print_response_report(response_df):
    if len(response_df) == 0:
        print("No response recommendations to display")
        return

    print("\n" + "=" * 100)
    print("SECURITY RESPONSE RECOMMENDATIONS")
    print("=" * 100)

    critical_count = len(response_df[response_df["action_priority"] == 1])
    high_count = len(response_df[response_df["action_priority"] == 2])
    medium_count = len(response_df[response_df["action_priority"] == 3])

    print("\nSUMMARY:")
    print(f"  Total incidents: {len(response_df)}")
    print(f"  Critical actions (Priority 1): {critical_count}")
    print(f"  High actions (Priority 2):     {high_count}")
    print(f"  Medium actions (Priority 3):   {medium_count}")

    for idx, incident in response_df.iterrows():
        print("\n" + "-" * 100)
        print(f"INCIDENT #{idx + 1} - PRIORITY {incident['action_priority']}")
        print("-" * 100)
        print(f"Source IP:          {incident.get('source_ip', 'N/A')}")
        print(f"Threat Type:        {incident['threat_type']}")
        print(f"Severity:           {incident.get('severity', 'N/A')}")
        print(f"Confidence:         {incident.get('avg_confidence', 0.0):.3f}")
        print(f"Alert Count:        {incident.get('alert_count', 0)}")

        print(f"\nPRIMARY ACTION:  {incident['primary_action']}")
        print(f"   Description:   {incident['action_description']}")
        print(f"   Automation:    {incident['automation_status']}")

    print("\n" + "=" * 100)


def export_for_soar(response_df, output_file="response_actions.csv"):
    soar_export = response_df[
        [
            "source_ip",
            "threat_type",
            "severity",
            "alert_count",
            "avg_confidence",
            "primary_action",
            "secondary_action",
            "action_priority",
            "automation_status",
            "ti_category",
            "ti_risk_level",
        ]
    ].copy()

    soar_export.to_csv(output_file, index=False)
    print(f"Exported {len(soar_export)} actions to {output_file}")
    return output_file


if __name__ == "__main__":
    sample_enriched = pd.DataFrame(
        {
            "source_ip": ["192.168.1.100", "10.0.0.50"],
            "time_window": ["2026-01-05 10:00:00", "2026-01-05 10:05:00"],
            "threat_type": ["brute_force", "malware"],
            "alert_count": [25, 5],
            "avg_confidence": [0.998, 0.995],
            "severity": ["MEDIUM", "HIGH"],
            "ti_category": ["Authentication Attack", "Malicious Software"],
            "ti_risk_level": ["MEDIUM", "HIGH"],
            "ti_impact": ["Account compromise", "System compromise"],
            "ti_mitigation": ["Block IP", "Isolate host"],
        }
    )

    response = recommend_response(sample_enriched)
    print_response_report(response)
    export_for_soar(response, "test_soar_actions.csv")
