"""
Generate realistic-looking security logs for testing
Creates diverse, believable log patterns similar to real production environments
"""
import pandas as pd
import random
from datetime import datetime, timedelta

# Realistic usernames
USERS = ['admin', 'jsmith', 'mjones', 'dbrown', 'kwilson', 'slee', 'rgarcia', 'aanderson', 'system', 'root']

# Realistic IP addresses
INTERNAL_IPS = [f"192.168.{random.randint(1,10)}.{random.randint(10,200)}" for _ in range(20)]
EXTERNAL_IPS = [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(10)]

# Realistic log templates
LOG_TEMPLATES = {
    'normal': [
        "User {user} logged in successfully from {ip}",
        "Authentication successful for user {user}",
        "User {user} accessed file {file}",
        "Session started for {user} from {ip}",
        "User {user} logged out successfully",
        "File {file} opened by {user}",
        "Configuration updated by {user}",
        "Backup completed successfully",
        "System health check passed",
        "Database connection established from {ip}",
    ],
    
    'brute_force': [
        "Failed password for {user} from {ip} port 22 ssh2",
        "Authentication failure for {user} from {ip}",
        "Invalid password attempt for user {user}",
        "Failed login attempt #{num} for {user} from {ip}",
        "Repeated authentication failures from {ip}",
        "Multiple failed SSH attempts detected from {ip}",
        "Account lockout triggered for {user} after {num} failed attempts",
        "Brute force pattern detected: {num} failed logins from {ip}",
    ],
    
    'malware': [
        "Suspicious executable {malware} detected in C:\\Temp",
        "Virus signature matched: {malware} in {file}",
        "Malicious process {malware}.exe terminated by antivirus",
        "Trojan detected: {malware} attempting network connection",
        "Quarantined file {file} - malware signature detected",
        "Security alert: {malware} found in user downloads folder",
        "Suspicious DLL injection attempt by process {malware}",
        "Malware hash {hash} detected in memory scan",
    ],
    
    'phishing': [
        "Email from {external_ip} flagged as phishing attempt",
        "Suspicious link clicked by user {user}: {url}",
        "Phishing email detected: credential harvesting attempt",
        "User {user} reported suspicious email requesting password",
        "Email with malicious attachment blocked from {external_ip}",
        "Fake login page detected: {url} impersonating internal portal",
        "Credential phishing attempt blocked for user {user}",
    ],
    
    'ddos': [
        "High volume of requests from {external_ip}: {num} req/sec",
        "DDoS attack detected: {num} connections from {external_ip}",
        "Rate limit exceeded from {external_ip}: {num} requests",
        "Abnormal traffic spike from single source {external_ip}",
        "Connection flood detected: {num} SYN packets from {external_ip}",
        "Service degradation: {num} concurrent connections from {external_ip}",
    ],
    
    'ransomware': [
        "Multiple files encrypted in {file} directory",
        "Suspicious file extension changes detected: {num} files to .encrypted",
        "Ransomware signature detected: mass file encryption in progress",
        "Critical: {num} files encrypted in last {time} minutes by {user}",
        "File encryption pattern detected: {file}",
        "Ransomware behavior: {num} files modified with encryption markers",
    ],
    
    'data_exfil': [
        "Large outbound data transfer detected: {num}GB to {external_ip}",
        "Unusual data upload: {num}MB transferred to external server {external_ip}",
        "Sensitive file {file} transferred to external IP {external_ip}",
        "Data exfiltration alert: {num}MB uploaded outside business hours",
        "Unauthorized data transfer to cloud storage {url}",
        "Bulk file download detected: {num} files by {user}",
    ],
    
    'insider_threat': [
        "User {user} accessed confidential files outside business hours",
        "Privileged account {user} accessed restricted database at {time}",
        "Unusual access pattern: {user} viewed {num} sensitive documents",
        "Admin {user} exported user database to external drive",
        "Suspicious activity: {user} accessed payroll data without authorization",
        "Role violation: {user} attempted to access executive files",
    ],
}

# Sample data for filling templates
MALWARE_NAMES = ['trojan.backdoor', 'win32.malware', 'cryptominer.exe', 'keylogger', 'ransomware.variant']
FILES = ['report.docx', 'budget.xlsx', 'credentials.txt', 'backup.zip', 'invoice.pdf', 'passwords.db']
URLS = ['http://phishing-site.com/login', 'http://malicious-domain.ru/steal', 'http://fake-bank.com']
HASHES = [f"{random.randint(100000, 999999):06x}" for _ in range(5)]


def generate_logs(num_logs=100, start_time=None):
    """
    Generate realistic security logs
    
    Args:
        num_logs: Number of log entries to generate
        start_time: Starting timestamp (default: 24 hours ago)
    
    Returns:
        DataFrame with columns: timestamp, source_ip, user, message, actual_threat
    """
    if start_time is None:
        start_time = datetime.now() - timedelta(hours=24)
    
    logs = []
    
    # Distribution: 40% normal, 60% threats
    threat_weights = {
        'normal': 0.40,
        'brute_force': 0.20,
        'malware': 0.15,
        'phishing': 0.10,
        'ddos': 0.05,
        'ransomware': 0.04,
        'data_exfil': 0.03,
        'insider_threat': 0.03,
    }
    
    for i in range(num_logs):
        # Select threat type based on weights
        threat_type = random.choices(
            list(threat_weights.keys()),
            weights=list(threat_weights.values())
        )[0]
        
        # Generate timestamp (spread over 24 hours)
        timestamp = start_time + timedelta(seconds=random.randint(0, 86400))
        
        # Select template and fill with realistic data
        template = random.choice(LOG_TEMPLATES[threat_type])
        
        # Fill template variables
        message = template.format(
            user=random.choice(USERS),
            ip=random.choice(INTERNAL_IPS),
            external_ip=random.choice(EXTERNAL_IPS),
            file=random.choice(FILES),
            malware=random.choice(MALWARE_NAMES),
            url=random.choice(URLS),
            hash=random.choice(HASHES),
            num=random.randint(3, 500),
            time=random.randint(1, 30)
        )
        
        # Create log entry
        logs.append({
            'timestamp': timestamp,
            'source_ip': random.choice(INTERNAL_IPS),
            'user': random.choice(USERS),
            'message': message,
            'actual_threat': threat_type  # Ground truth for comparison
        })
    
    # Sort by timestamp
    df = pd.DataFrame(logs)
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df


def save_logs_csv(df, filename='realistic_logs.csv'):
    """Save generated logs to CSV"""
    df.to_csv(filename, index=False)
    print(f"✅ Saved {len(df)} logs to {filename}")
    
    print(f"\n📊 Log Distribution:")
    print(df['actual_threat'].value_counts())
    
    return filename


if __name__ == "__main__":
    print("="*80)
    print("🔧 REALISTIC LOG GENERATOR")
    print("="*80)
    
    # Generate logs
    print("\n⚙️  Generating 200 realistic security logs...")
    df = generate_logs(num_logs=200)
    
    # Save to CSV
    filename = save_logs_csv(df, 'data/realistic_logs.csv')
    
    print(f"\n📝 Sample logs:")
    print("-"*80)
    print(df[['timestamp', 'user', 'message', 'actual_threat']].head(10).to_string(index=False))
    
    print("\n" + "="*80)
    print(f"✅ Ready to test! Use: python test_real_logs.py csv {filename}")
    print("="*80)
