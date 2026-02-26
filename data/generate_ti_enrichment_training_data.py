"""
Generate training data for TI enrichment model.
Creates labeled incident text samples mapped to TI profiles.
"""
import csv
import os
import random
from datetime import datetime


OUTPUT_PATH = "data/training/csv/ti_enrichment/ti_enrichment_dataset.csv"
SAMPLES_PER_CLASS = 500

TI_PROFILES = {
	"brute_force": {
		"category": "Authentication Attack",
		"risk_level": "MEDIUM",
		"impact": "Account compromise, unauthorized access",
		"mitigation": "Enable MFA, implement account lockout, monitor failed logins",
		"indicators": [
			"multiple failed logins",
			"invalid credentials",
			"account lockout",
		],
	},
	"malware": {
		"category": "Malicious Software",
		"risk_level": "HIGH",
		"impact": "System compromise, data theft",
		"mitigation": "Isolate host, run antivirus scan, analyze malware",
		"indicators": [
			"suspicious process",
			"malware signature",
			"file hash match",
		],
	},
	"phishing": {
		"category": "Social Engineering",
		"risk_level": "MEDIUM",
		"impact": "Credential theft, account takeover",
		"mitigation": "Block URLs, user training, email filtering",
		"indicators": [
			"suspicious email",
			"credential request",
			"spoofed sender",
		],
	},
	"ddos": {
		"category": "Denial of Service",
		"risk_level": "MEDIUM",
		"impact": "Service unavailability",
		"mitigation": "Enable DDoS protection, rate limiting",
		"indicators": [
			"traffic spike",
			"request flood",
			"bandwidth saturation",
		],
	},
	"ransomware": {
		"category": "Extortion Malware",
		"risk_level": "HIGH",
		"impact": "Data encryption and loss",
		"mitigation": "Isolate immediately, restore from backup",
		"indicators": [
			"file encryption",
			"ransom note",
			"mass file changes",
		],
	},
	"data_exfil": {
		"category": "Data Breach",
		"risk_level": "HIGH",
		"impact": "Data loss and breach",
		"mitigation": "Block external connections",
		"indicators": [
			"large outbound transfer",
			"unusual upload",
			"external connection",
		],
	},
	"insider_threat": {
		"category": "Insider Activity",
		"risk_level": "HIGH",
		"impact": "Privilege abuse and theft",
		"mitigation": "Review permissions and disable account",
		"indicators": [
			"after-hours access",
			"privilege escalation",
			"sensitive data access",
		],
	},
	"normal": {
		"category": "Normal Activity",
		"risk_level": "LOW",
		"impact": "No impact",
		"mitigation": "Continue monitoring",
		"indicators": [
			"normal login",
			"routine operations",
			"scheduled task",
		],
	},
}


def build_text(threat_type, indicators):
	indicators_text = ", ".join(indicators)
	return f"Incident type: {threat_type}. Indicators: {indicators_text}."


def main():
	random.seed(42)
	os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

	with open(OUTPUT_PATH, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(
			[
				"threat_type",
				"timestamp",
				"ti_category",
				"ti_risk_level",
				"ti_impact",
				"ti_mitigation",
				"label",
				"text",
			]
		)

		for threat_type, profile in TI_PROFILES.items():
			for _ in range(SAMPLES_PER_CLASS):
				indicators = random.sample(profile["indicators"], k=2)
				text = build_text(threat_type, indicators)
				label = f"{threat_type}|{profile['risk_level']}"
				writer.writerow(
					[
						threat_type,
						datetime.now().isoformat(),
						profile["category"],
						profile["risk_level"],
						profile["impact"],
						profile["mitigation"],
						label,
						text,
					]
				)

	print(f"Wrote {SAMPLES_PER_CLASS * len(TI_PROFILES)} samples to {OUTPUT_PATH}")


if __name__ == "__main__":
	main()
