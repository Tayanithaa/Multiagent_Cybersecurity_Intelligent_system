"""
Generate training data for response recommendation model.
Creates labeled samples for recommended actions.
"""
import csv
import os
import random
from datetime import datetime


OUTPUT_PATH = "data/training/csv/response/response_agent_training.csv"
SAMPLES = 1000

THREAT_TYPES = [
	"brute_force",
	"malware",
	"phishing",
	"ddos",
	"ransomware",
	"data_exfil",
	"insider_threat",
]

SEVERITIES = ["LOW", "MEDIUM", "HIGH"]

ACTION_MAP = {
	"ransomware": ("ISOLATE_HOST", 1),
	"malware": ("SCAN_SYSTEM", 2),
	"phishing": ("BLOCK_URL", 2),
	"ddos": ("ESCALATE", 2),
	"data_exfil": ("BLOCK_IP", 1),
	"insider_threat": ("DISABLE_ACCOUNT", 1),
	"brute_force": ("RESET_PASSWORD", 2),
}


def main():
	random.seed(42)
	os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

	with open(OUTPUT_PATH, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(
			[
				"threat_type",
				"severity",
				"confidence",
				"alert_count",
				"recommended_action",
				"action_priority",
				"timestamp",
			]
		)

		for _ in range(SAMPLES):
			threat_type = random.choice(THREAT_TYPES)
			severity = random.choice(SEVERITIES)
			confidence = round(random.uniform(0.6, 0.99), 3)
			alert_count = random.randint(1, 50)

			action, priority = ACTION_MAP[threat_type]
			if severity == "HIGH" and confidence > 0.9:
				priority = 1
			elif severity == "LOW":
				priority = max(priority, 3)

			writer.writerow(
				[
					threat_type,
					severity,
					confidence,
					alert_count,
					action,
					priority,
					datetime.now().isoformat(),
				]
			)

	print(f"Wrote {SAMPLES} samples to {OUTPUT_PATH}")


if __name__ == "__main__":
	main()
