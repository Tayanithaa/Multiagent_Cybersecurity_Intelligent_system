"""
CORRELATION MODEL AGENT
Uses RoBERTa to predict whether alerts should be correlated.
"""
import json
import os
import warnings

import pandas as pd
import torch
from transformers import RobertaForSequenceClassification, RobertaTokenizer

warnings.filterwarnings("ignore")


class CorrelationRoBERTaModel:
    """RoBERTa-based correlation model for alert pairing."""

    def __init__(self, model_path="models/correlation_roberta"):
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        config_file = os.path.join(model_path, "config.json")
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Model config not found at {config_file}. "
                "Please train the model first using train_correlation_roberta_model.py"
            )

        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.label_map = self.config["label_map"]
        self.id_to_label = {int(k): v for k, v in self.config["id_to_label"].items()}
        self.max_length = self.config["max_length"]
        self.positive_label_id = self.label_map.get("yes", 1)

        self.tokenizer = RobertaTokenizer.from_pretrained(model_path)
        self.model = RobertaForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()

    def _predict_pairs(self, texts, batch_size=32):
        probabilities = []
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
                probs = torch.softmax(outputs.logits, dim=-1)
            probabilities.extend(probs[:, self.positive_label_id].cpu().numpy().tolist())
        return probabilities


class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1


_global_correlation_model = None


def _build_pair_text(threat_type, ip_a, ip_b, time_diff_minutes):
    return (
        f"Threat {threat_type} between {ip_a} and {ip_b}. "
        f"Time difference {time_diff_minutes} minutes."
    )


def correlate_alerts(df, time_window="5min", model_path="models/correlation_roberta", threshold=0.5):
    if df is None or len(df) == 0:
        return pd.DataFrame()

    data = df.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"])

    ip_col = "source_ip" if "source_ip" in data.columns else "ip"
    threat_col = "bert_class" if "bert_class" in data.columns else "threat_type"
    confidence_col = "bert_confidence" if "bert_confidence" in data.columns else "avg_confidence"

    threats = data[data[threat_col] != "normal"].copy()
    if len(threats) == 0:
        print("No threats detected - all logs are normal activity")
        return pd.DataFrame()

    global _global_correlation_model
    if _global_correlation_model is None:
        _global_correlation_model = CorrelationRoBERTaModel(model_path)

    time_delta = pd.to_timedelta(time_window)
    threats = threats.sort_values("timestamp").reset_index(drop=True)

    pair_texts = []
    pair_indices = []

    for threat_type, group in threats.groupby(threat_col):
        group = group.sort_values("timestamp").reset_index()
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                time_diff = group.loc[j, "timestamp"] - group.loc[i, "timestamp"]
                if time_diff > time_delta:
                    break
                minutes = int(time_diff.total_seconds() / 60)
                text = _build_pair_text(
                    threat_type,
                    group.loc[i, ip_col],
                    group.loc[j, ip_col],
                    minutes,
                )
                pair_texts.append(text)
                pair_indices.append((group.loc[i, "index"], group.loc[j, "index"]))

    if not pair_texts:
        return pd.DataFrame()

    probs = _global_correlation_model._predict_pairs(pair_texts)

    uf = UnionFind(len(threats))
    index_map = {idx: pos for pos, idx in enumerate(threats.index.tolist())}

    for (idx_a, idx_b), prob in zip(pair_indices, probs):
        if prob >= threshold:
            uf.union(index_map[idx_a], index_map[idx_b])

    clusters = {}
    for pos in range(len(threats)):
        root = uf.find(pos)
        clusters.setdefault(root, []).append(pos)

    incidents = []
    for members in clusters.values():
        cluster_df = threats.iloc[members]
        users = list(set(cluster_df.get("user", pd.Series(dtype=str)).dropna().tolist()))
        threat_type = cluster_df[threat_col].mode()[0]
        severity = cluster_df.get("severity", pd.Series(["MEDIUM"])).mode()[0]
        avg_confidence = cluster_df[confidence_col].mean()
        alert_count = len(cluster_df)
        source_ip = cluster_df[ip_col].mode()[0]
        time_window_value = cluster_df["timestamp"].min().floor(time_window)

        incidents.append(
            {
                "source_ip": source_ip,
                "time_window": time_window_value,
                "threat_type": threat_type,
                "alert_count": alert_count,
                "avg_confidence": avg_confidence,
                "severity": severity,
                "users": users,
                "user_count": len(users),
            }
        )

    incidents_df = pd.DataFrame(incidents)
    if len(incidents_df) == 0:
        return incidents_df

    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    incidents_df["severity_rank"] = incidents_df["severity"].map(severity_order)
    incidents_df = incidents_df.sort_values(["severity_rank", "alert_count"], ascending=[True, False])
    incidents_df = incidents_df.drop("severity_rank", axis=1)

    return incidents_df


def get_incident_summary(incidents):
    if incidents is None or len(incidents) == 0:
        return {
            "total_incidents": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0,
            "threat_breakdown": {},
        }

    return {
        "total_incidents": len(incidents),
        "high_severity": len(incidents[incidents["severity"] == "HIGH"]),
        "medium_severity": len(incidents[incidents["severity"] == "MEDIUM"]),
        "low_severity": len(incidents[incidents["severity"] == "LOW"]),
        "threat_breakdown": incidents["threat_type"].value_counts().to_dict(),
        "avg_alerts_per_incident": incidents["alert_count"].mean(),
        "max_alerts_in_incident": incidents["alert_count"].max(),
    }


def print_incident_report(incidents, alerts_df):
    if incidents is None or len(incidents) == 0:
        print("No incidents detected")
        return

    print("\n" + "=" * 80)
    print("SECURITY INCIDENTS REPORT")
    print("=" * 80)
    print(
        f"{'IP':<16} {'Time Window':<20} {'Users':<6} {'Threat Type':<15} "
        f"{'Alerts':<8} {'Confidence':<12} {'Severity'}"
    )
    print("-" * 80)

    for _, inc in incidents.iterrows():
        print(
            f"{inc['source_ip']:<16} "
            f"{str(inc['time_window']):<20} "
            f"{inc['user_count']:<6} "
            f"{inc['threat_type']:<15} "
            f"{inc['alert_count']:<8} "
            f"{inc['avg_confidence']:<12.3f} "
            f"{inc['severity']}"
        )

    summary = get_incident_summary(incidents)

    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    print(f"Total Logs Processed:           {len(alerts_df)}")
    print(f"Total Incidents Detected:       {summary['total_incidents']}")
    if summary["total_incidents"] > 0:
        print(f"Incident Reduction Ratio:    {len(alerts_df)/summary['total_incidents']:.1f}x")

    print("\nIncident Breakdown by Threat Type:")
    for threat, count in sorted(summary["threat_breakdown"].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {threat:<15}:  {count} incident(s)")

    print("\nIncident Breakdown by Severity:")
    print(f"  - HIGH           :  {summary['high_severity']} incident(s)")
    print(f"  - MEDIUM         :  {summary['medium_severity']} incident(s)")
    print(f"  - LOW            :  {summary['low_severity']} incident(s)")

    print("\nTop 3 Highest-Alert Incidents:")
    top_3 = incidents.nlargest(3, "alert_count")
    for _, inc in top_3.iterrows():
        print(
            f"  - {inc['source_ip']:<15} | {inc['threat_type']:<12} | "
            f"{inc['alert_count']:3} alerts | {inc['severity']}"
        )

    print("=" * 80)


if __name__ == "__main__":
    print("=" * 80)
    print("TESTING CORRELATION MODEL")
    print("=" * 80)

    sample_data = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-04 10:00", periods=20, freq="1min"),
            "source_ip": ["192.168.1.10"] * 10 + ["192.168.1.20"] * 10,
            "user": ["admin"] * 20,
            "bert_class": ["brute_force"] * 8 + ["normal"] * 2 + ["malware"] * 10,
            "bert_confidence": [0.95] * 20,
            "severity": ["MEDIUM"] * 10 + ["HIGH"] * 10,
        }
    )

    incidents = correlate_alerts(sample_data, time_window="5min")
    print_incident_report(incidents, sample_data)
