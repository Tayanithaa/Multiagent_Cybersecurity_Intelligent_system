import pandas as pd
from datetime import datetime, timedelta

# Load parquet
df = pd.read_parquet("C:\\Projects\\converter\\kaggle\\Benign-Monday-no-metadata.parquet")

# Generate timestamps (starting from current time, incrementing by 1 second per row)
base_time = datetime.now()
timestamps = [base_time + timedelta(seconds=i) for i in range(len(df))]

# Create SOC-style logs
logs_df = pd.DataFrame({
    "timestamp": timestamps,
    "user": "unknown",
    "protocol": df["Protocol"],
    "event_type": "NETWORK_FLOW",
    "status": df["Label"].apply(
        lambda x: "SUCCESS" if x.lower() in ["benign", "normal"] else "ANOMALOUS"
    ),
    "flow_duration_ms": df["Flow Duration"],
    "total_packets": df["Total Fwd Packets"] + df["Total Backward Packets"],
    "total_bytes": df["Fwd Packets Length Total"] + df["Bwd Packets Length Total"],
    "raw_message": df.apply(
        lambda r: (
            f"Network flow: protocol={r['Protocol']} duration={r['Flow Duration']}ms "
            f"fwd_packets={r['Total Fwd Packets']} bwd_packets={r['Total Backward Packets']} "
            f"label={r['Label']}"
        ),
        axis=1
    )
})

# Save as CSV
logs_df.to_csv("converted_logs.csv", index=False)

print("✅ Parquet converted to SOC-style logs")
