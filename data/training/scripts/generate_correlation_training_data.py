"""
Generate training data for correlation model.
Creates pairwise alert examples with binary correlation labels.
"""
import csv
import os
import random
from datetime import datetime, timedelta


OUTPUT_PATH = "data/training/csv/correlation/correlation_dataset.csv"
SAMPLES = 5000
THREAT_TYPES = [
	"brute_force",
	"malware",
	"phishing",
	"ddos",
	"ransomware",
	"data_exfil",
	"insider_threat",
]


def random_ip():
	return f"192.168.{random.randint(1, 50)}.{random.randint(1, 254)}"


def random_time(base):
	return base + timedelta(minutes=random.randint(-180, 180))


def build_text(threat_type, ip_a, ip_b, time_diff):
	return (
		f"Threat {threat_type} between {ip_a} and {ip_b}. "
		f"Time difference {time_diff} minutes."
	)


def main():
	random.seed(42)
	os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

	base_time = datetime.now()

	with open(OUTPUT_PATH, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(
			[
				"alert1_ip",
				"alert2_ip",
				"time_diff_minutes",
				"threat_type",
				"correlation_text",
				"should_correlate",
			]
		)

		for _ in range(SAMPLES):
			threat_type = random.choice(THREAT_TYPES)

			ip_a = random_ip()
			same_ip = random.random() < 0.6
			ip_b = ip_a if same_ip else random_ip()

			time_a = random_time(base_time)
			close_time = random.random() < 0.6
			if close_time:
				time_b = time_a + timedelta(minutes=random.randint(0, 5))
			else:
				time_b = time_a + timedelta(minutes=random.randint(30, 120))

			time_diff = int(abs((time_b - time_a).total_seconds()) / 60)

			should_correlate = 1 if same_ip and close_time else 0
			text = build_text(threat_type, ip_a, ip_b, time_diff)

			writer.writerow([ip_a, ip_b, time_diff, threat_type, text, should_correlate])

	print(f"Wrote {SAMPLES} samples to {OUTPUT_PATH}")


if __name__ == "__main__":
	main()
