BANDWIDTH_GBPS = 100
LATENCY_US = 20

message_sizes = [
    256,
    1024,
    4096,
    16384,
]

queue_depths = [
    1, 2, 4, 8, 16, 32,
    64, 128, 256, 512, 1024
]

latency_seconds = LATENCY_US / 1_000_000

bandwidth_bits_per_sec = (
    BANDWIDTH_GBPS * 1_000_000_000
)

bdp_bytes = (
    bandwidth_bits_per_sec
    * latency_seconds
    / 8
)

print(f"Bandwidth : {BANDWIDTH_GBPS} Gbit/s")
print(f"Latency   : {LATENCY_US} us")
print(f"BDP       : {bdp_bytes:,.0f} bytes")
print()

for message_size in message_sizes:

    print(f"Message Size: {message_size:,} bytes")
    print("QD    In-Flight Bytes    Throughput Gbit/s")
    print("------------------------------------------")

    for qd in queue_depths:

        in_flight_bytes = message_size * qd

        modeled_throughput = (
            in_flight_bytes * 8
            / latency_seconds
            / 1_000_000_000
        )

        throughput_gbps = min(
            modeled_throughput,
            BANDWIDTH_GBPS
        )

        print(
            f"{qd:<5} "
            f"{in_flight_bytes:>15,} "
            f"{throughput_gbps:>18.2f}"
        )

    print()
