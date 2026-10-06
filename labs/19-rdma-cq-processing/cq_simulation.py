WR_RATE = 2_000_000
PROCESSING_CAPACITY = 1_200_000
DURATION = 10

signal_intervals = [1, 2, 4, 8, 16]

print(
    "Signal Every | Completion Rate | "
    "Processed/sec | Backlog after 10s"
)
print("-" * 70)

for interval in signal_intervals:
    completion_rate = WR_RATE // interval
    backlog = 0

    for _ in range(DURATION):
        available = backlog + completion_rate

        processed = min(
            PROCESSING_CAPACITY,
            available
        )

        backlog = available - processed

    print(
        f"{interval:>12} | "
        f"{completion_rate:>15,} | "
        f"{processed:>13,} | "
        f"{backlog:>17,}"
    )
