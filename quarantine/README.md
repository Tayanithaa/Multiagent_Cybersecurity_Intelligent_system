# Quarantine Directory - Malware Sample Storage

⚠️ **WARNING: This directory contains potentially malicious files!**

## Purpose

This directory stores uploaded malware samples in a safe, isolated environment with read-only permissions.

## Structure

```
quarantine/
├── pending/      # Files awaiting analysis
├── analyzed/     # Files that have been analyzed
└── rejected/     # Files that failed validation
```

## Security Measures

1. **No Execution**: Files in this directory are NEVER executed on this machine
2. **Read-Only**: All files stored with `0o444` permissions
3. **Isolated): Physical network separation for actual analysis
4. **Hash-Based Naming**: Files named by SHA256 hash for tracking

## File Naming Convention

Files are stored using their SHA256 hash:
```
pending/a1b2c3d4e5f6...
```

## Access Control

- Only the sandbox submission handler can write to this directory
- All uploaded files are immediately set to read-only
- Files are deleted after successful analysis or after retention period

## Retention Policy

- **Pending**: Kept until analysis completes
- **Analyzed**: Kept for 30 days for audit purposes
- **Rejected**: Kept for 7 days for review

## DO NOT

❌ Open files from this directory  
❌ Execute any files  
❌ Copy files outside quarantine without sanitization  
❌ Share files without proper authorization  

## Cleanup

To manually clean quarantine:
```bash
# Remove old analyzed files (30+ days)
find quarantine/analyzed/ -mtime +30 -delete

# Remove old rejected files (7+ days)
find quarantine/rejected/ -mtime +7 -delete
```

---

**Remember:** These are potentially dangerous files. Handle with extreme caution!
