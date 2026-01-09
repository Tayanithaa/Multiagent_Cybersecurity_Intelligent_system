"""
STEP 1: Generate Large Labeled Dataset for Training
Run this first to create training data
"""
import pandas as pd
import random
from datetime import datetime, timedelta
import os

# Configuration
SAMPLES_PER_CLASS = 1000  # Increase for better model
OUTPUT_DIR = "data/training"
os.makedirs(OUTPUT_DIR, exist_ok=True)

USERS = ["alice", "bob", "charlie", "david", "eve", "admin", "user1", "user2", "user3", "system"]
IPS = [f"192.168.{i}.{j}" for i in range(1, 50) for j in range(1, 250, 10)]
EMAILS = ["hr@company.com", "it@company.com", "admin@corp.com", "security@company.com"]

def random_time():
    base = datetime.now()
    return base - timedelta(minutes=random.randint(1, 50000))

# ==============================================================================
# THREAT CLASS TEMPLATES - Diverse realistic messages
# ==============================================================================

NORMAL_TEMPLATES = [
    "User logged in successfully",
    "Session established for user {user}",
    "File {file} accessed successfully",
    "Routine system check completed",
    "Database backup completed successfully",
    "Email sent to {email}",
    "Application started normally",
    "User logout successful",
    "File saved: {file}",
    "System health check passed",
    "Scheduled task executed successfully",
    "User profile updated",
    "Report generated successfully",
    "Connection established to database",
    "Cache cleared successfully",
]

BRUTE_FORCE_TEMPLATES = [
    "Multiple failed login attempts detected",
    "Failed login attempt #{attempt} for user {user}",
    "Authentication failed: invalid password",
    "Login denied: too many failed attempts",
    "Suspicious login pattern detected from {ip}",
    "Account locked due to multiple failures",
    "Failed SSH login attempt from {ip}",
    "Invalid credentials provided for {user}",
    "Password authentication failed for {user}",
    "Brute force attack detected from {ip}",
    "Repeated login failures: {user}@{ip}",
    "Login rate limit exceeded from {ip}",
]

MALWARE_TEMPLATES = [
    "Suspicious executable detected in temp directory",
    "Malicious process {process} terminated",
    "Virus signature detected in file {file}",
    "Trojan detected: {file}",
    "Ransomware behavior detected",
    "Suspicious registry modification detected",
    "Malware hash match: {hash}",
    "Backdoor communication detected to {ip}",
    "Suspicious DLL injection attempt",
    "Rootkit activity detected",
    "Command and control traffic detected",
    "Malicious script execution blocked",
    "Potentially unwanted program detected",
]

PHISHING_TEMPLATES = [
    "Email contains malicious link asking for credentials",
    "Suspicious email from {email} with credential request",
    "Phishing attempt detected: fake login page",
    "Email with spoofed sender detected",
    "Malicious attachment in email from {email}",
    "Credential harvesting attempt detected",
    "Suspicious URL in email: {url}",
    "Email impersonation detected",
    "Phishing link clicked by user {user}",
    "Fake invoice email detected",
    "Spear phishing attempt targeting {user}",
]

DDOS_TEMPLATES = [
    "High volume of requests detected from single IP",
    "DDoS attack detected: {requests} requests/sec from {ip}",
    "Network bandwidth saturated from {ip}",
    "SYN flood detected from {ip}",
    "Unusual traffic spike from {ip}",
    "UDP flood detected: source {ip}",
    "HTTP flood attack in progress",
    "Distributed denial of service detected",
    "Connection flood from {ip}",
    "Abnormal request rate: {requests} req/s",
]

RANSOMWARE_TEMPLATES = [
    "Multiple files encrypted in short time interval",
    "Ransomware detected: {files} files encrypted",
    "Suspicious file encryption activity",
    "Mass file modification detected",
    "Encryption pattern matches ransomware",
    "Ransom note file detected: README.txt",
    "Crypto-locker behavior detected",
    "Files renamed with .encrypted extension",
    "Shadow copy deletion detected",
    "Bulk file encryption in progress",
]

DATA_EXFIL_TEMPLATES = [
    "Large outbound data transfer to external server",
    "Unusual data upload to {ip}: {size}MB",
    "Sensitive data accessed and transferred",
    "Database dump detected to external IP",
    "Large file transfer to cloud storage",
    "Data exfiltration detected: {files} files uploaded",
    "Unauthorized data transfer to {ip}",
    "Confidential files copied to external drive",
    "Suspicious outbound traffic: {size}GB transferred",
    "Data leak detected to external server",
]

INSIDER_THREAT_TEMPLATES = [
    "Admin accessed confidential files outside business hours",
    "Privilege escalation detected for {user}",
    "Unauthorized access to sensitive database",
    "User {user} accessed HR records without authorization",
    "Suspicious file access by privileged user",
    "Admin account used from unusual location",
    "Confidential data accessed at {time}",
    "Unauthorized database query by {user}",
    "Sensitive file download by {user} after hours",
    "Privilege abuse detected: {user}",
]

# ==============================================================================
# LABEL MAPPING
# ==============================================================================
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

def generate_class_data(class_name, templates, count):
    """Generate diverse data for a threat class"""
    rows = []
    
    for i in range(count):
        template = random.choice(templates)
        
        # Fill template variables
        message = template.format(
            user=random.choice(USERS),
            ip=random.choice(IPS),
            email=random.choice(EMAILS),
            file=random.choice(["report.pdf", "data.xlsx", "config.ini", "backup.zip", "malware.exe"]),
            process=random.choice(["svchost.exe", "explorer.exe", "malware.exe", "trojan.dll"]),
            hash=f"md5:{random.randint(1000000, 9999999)}",
            url=f"http://phishing-site-{random.randint(1, 999)}.com",
            requests=random.randint(1000, 50000),
            files=random.randint(10, 1000),
            size=random.randint(100, 5000),
            attempt=random.randint(1, 20),
            time=f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"
        )
        
        rows.append({
            "timestamp": random_time(),
            "user": random.choice(USERS),
            "ip": random.choice(IPS),
            "raw_message": message,
            "label": class_name,
            "label_id": LABEL_MAP[class_name]
        })
    
    return rows

# ==============================================================================
# GENERATE ALL CLASSES
# ==============================================================================
print("🚀 Generating training dataset...")
print(f"📊 {SAMPLES_PER_CLASS} samples per class × 8 classes = {SAMPLES_PER_CLASS * 8} total samples\n")

all_data = []

print("Generating NORMAL logs...")
all_data.extend(generate_class_data("normal", NORMAL_TEMPLATES, SAMPLES_PER_CLASS))

print("Generating BRUTE_FORCE logs...")
all_data.extend(generate_class_data("brute_force", BRUTE_FORCE_TEMPLATES, SAMPLES_PER_CLASS))

print("Generating MALWARE logs...")
all_data.extend(generate_class_data("malware", MALWARE_TEMPLATES, SAMPLES_PER_CLASS))

print("Generating PHISHING logs...")
all_data.extend(generate_class_data("phishing", PHISHING_TEMPLATES, SAMPLES_PER_CLASS))

print("Generating DDOS logs...")
all_data.extend(generate_class_data("ddos", DDOS_TEMPLATES, SAMPLES_PER_CLASS))

print("Generating RANSOMWARE logs...")
all_data.extend(generate_class_data("ransomware", RANSOMWARE_TEMPLATES, SAMPLES_PER_CLASS))

print("Generating DATA_EXFIL logs...")
all_data.extend(generate_class_data("data_exfil", DATA_EXFIL_TEMPLATES, SAMPLES_PER_CLASS))

print("Generating INSIDER_THREAT logs...")
all_data.extend(generate_class_data("insider_threat", INSIDER_THREAT_TEMPLATES, SAMPLES_PER_CLASS))

# ==============================================================================
# SAVE DATASET
# ==============================================================================
df = pd.DataFrame(all_data)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # Shuffle

output_path = os.path.join(OUTPUT_DIR, "full_dataset.csv")
df.to_csv(output_path, index=False)

print(f"\n✅ Dataset saved to: {output_path}")
print(f"📊 Total samples: {len(df)}")
print(f"\n📈 Class distribution:")
print(df['label'].value_counts().sort_index())
print(f"\n✅ Ready for training! Run train_bert_model.py next.")
