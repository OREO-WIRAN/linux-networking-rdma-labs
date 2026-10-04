MESSAGE_SIZE = 256          # bytes
LATENCY_US = 20              # microseconds per operation
MAX_GBPS = 100               # simulated link capacity

queue_depths = [1, 8, 16, 30, 32, 60, 61, 62, 64, 128]

print("QD\tOps/sec\t\tThroughput (Gbps)")

for qd in queue_depths:
    latency_seconds = LATENCY_US / 1_000_000

    # Simplified model:
    # outstanding operations / latency
    ops_per_sec = qd / latency_seconds

    # Convert payload rate to Gbit/s
    throughput_gbps = (
        ops_per_sec * MESSAGE_SIZE * 8
    ) / 1_000_000_000

    # Apply simulated link-capacity ceiling
    throughput_gbps = min(throughput_gbps, MAX_GBPS)

    print(f"{qd}\t{ops_per_sec:,.0f}\t\t{throughput_gbps:.2f}")
