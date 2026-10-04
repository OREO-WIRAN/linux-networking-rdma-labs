# Lab 18 — RDMA Queue Depth, Concurrency, and Throughput

## Objective

Study how queue depth (QD), latency, message size, and available
link capacity interact in a simplified RDMA-style performance model.

This lab focuses on performance-engineering reasoning rather than
real RDMA hardware benchmarking.

The current WSL2 environment does not expose an RDMA device, so the
experiment uses a Python simulation.

---

## Core Concept

Queue Depth represents the number of operations that may be
outstanding or in-flight.

A simplified model used in this lab is:

```text
Ops/sec ≈ Queue Depth / Latency
```

Payload throughput is then estimated as:

```text
Throughput ≈ Ops/sec × Message Size × 8
```

The result is capped by the simulated link capacity.

Important:

Higher queue depth does not reduce the latency of an individual
operation.

Instead, additional concurrency can allow more operations to remain
in-flight and improve aggregate throughput.

---

## Simulation

File:

```text
qd_simulation.py
```

Initial parameters:

```text
MESSAGE_SIZE = 4096 bytes
LATENCY_US   = 10 us
MAX_GBPS     = 100 Gbps
```

### Experiment 1 — Increasing Queue Depth

Observed results included:

```text
QD     Ops/sec       Throughput
1       100,000        3.28 Gbps
2       200,000        6.55 Gbps
4       400,000       13.11 Gbps
8       800,000       26.21 Gbps
16    1,600,000       52.43 Gbps
30    3,000,000       98.30 Gbps
31    3,100,000      100.00 Gbps
32    3,200,000      100.00 Gbps
64    6,400,000      100.00 Gbps
```

### Observation

At low QD, there is not enough concurrency to use the full simulated
link capacity.

Increasing QD increases the number of operations in-flight and raises
aggregate throughput.

Around QD 31, the model reaches the 100 Gbps link-capacity ceiling.

Increasing QD beyond this point does not increase throughput in this
model.

```text
Insufficient concurrency
        ↓
Increase QD
        ↓
More work in-flight
        ↓
Higher aggregate throughput
        ↓
Reach link-capacity ceiling
        ↓
Further QD increase gives no additional throughput
```

This demonstrates bottleneck migration.

Before saturation, concurrency is the limiting factor.

After saturation, the configured link capacity becomes the limiting
factor.

---

## Experiment 2 — Increasing Latency

Latency was changed from:

```text
10 us → 20 us
```

Message size remained:

```text
4096 bytes
```

Selected results:

```text
QD     Ops/sec       Throughput
1        50,000        1.64 Gbps
8       400,000       13.11 Gbps
16      800,000       26.21 Gbps
30    1,500,000       49.15 Gbps
32    1,600,000       52.43 Gbps
60    3,000,000       98.30 Gbps
61    3,050,000       99.94 Gbps
62    3,100,000      100.00 Gbps
64    3,200,000      100.00 Gbps
128   6,400,000      100.00 Gbps
```

### Observation

With 10 us latency:

```text
QD ≈ 31 → 100 Gbps
```

With 20 us latency:

```text
QD ≈ 62 → 100 Gbps
```

Doubling latency required approximately twice the queue depth to
recover the same aggregate throughput in this simplified model.

However, increasing QD did not reduce individual operation latency.

Therefore:

```text
Throughput recovery != Latency recovery
```

Concurrency can help hide latency from an aggregate-throughput
perspective, but it does not make an individual operation complete
faster.

---

## Experiment 3 — Small Messages

Parameters:

```text
MESSAGE_SIZE = 256 bytes
LATENCY_US   = 20 us
MAX_GBPS     = 100 Gbps
```

Observed results:

```text
QD     Ops/sec       Throughput
1        50,000        0.10 Gbps
8       400,000        0.82 Gbps
16      800,000        1.64 Gbps
30    1,500,000        3.07 Gbps
32    1,600,000        3.28 Gbps
60    3,000,000        6.14 Gbps
61    3,050,000        6.25 Gbps
62    3,100,000        6.35 Gbps
64    3,200,000        6.55 Gbps
128   6,400,000       13.11 Gbps
```

At QD 62:

```text
4096-byte message → 100.00 Gbps
256-byte message  →   6.35 Gbps
```

The same queue depth does not guarantee the same throughput.

With smaller messages, each operation carries less payload, so a much
higher operation rate is required to fill the same link capacity.

---

## Performance Engineering Interpretation

Low throughput does not automatically mean that the network link is
broken or saturated.

For example:

```text
Link capacity = 100 Gbps
Throughput    = 6.35 Gbps
Packet loss   = 0
Message size  = 256 bytes
Latency       = 20 us
QD            = 62
```

It would be incorrect to immediately conclude that the network is the
bottleneck.

The workload may simply be unable to generate enough payload rate due
to factors such as:

- message size
- latency
- available concurrency
- operation rate
- CPU processing
- completion processing
- application communication pattern

---

## RDMA Connection

In real RDMA systems, applications post Work Requests to Queue Pairs.

Multiple operations can be outstanding at the same time.

Queue depth therefore affects how much work can remain in-flight.

However, real RDMA performance also depends on many factors not
modeled here, including:

- RNIC capabilities
- PCIe bandwidth
- memory bandwidth
- MTU and packetization
- CQ processing
- CPU posting and polling overhead
- congestion
- transport behavior
- application synchronization
- GPU synchronization
- communication pattern

Therefore, this simulation should not be interpreted as an RDMA
hardware benchmark.

---

## Engineering Takeaways

1. Link capacity is not the same as application throughput.

2. Queue depth controls available concurrency.

3. Too little concurrency can leave link capacity unused.

4. Increasing QD can improve aggregate throughput by keeping more
   operations in-flight.

5. Once another resource reaches saturation, increasing QD further
   may provide no additional throughput.

6. Higher QD is not automatically better.

7. Higher latency may require more concurrency to maintain the same
   aggregate throughput.

8. Increasing concurrency does not remove individual-operation
   latency.

9. Small messages may require very high operation rates to utilize a
   high-bandwidth link.

10. Low link utilization does not automatically prove a network
    failure or network bottleneck.

---

## Troubleshooting Mindset

When throughput is lower than expected, do not immediately blame the
network.

Measure and investigate:

```text
Throughput
Latency
Message size
Queue depth
Operations/sec
CPU utilization
Completion processing
Network errors
Application communication pattern
```

The engineering principle is:

```text
Do not guess the bottleneck.
Measure, form a hypothesis, test it, and verify with evidence.
```

---

## Lab Limitation

This lab uses a mathematical Python simulation.

No real RDMA device, RNIC, Queue Pair, Completion Queue, or RDMA
traffic was exercised in this experiment.

The purpose is to build intuition for queue depth, concurrency,
latency, message size, saturation, and bottleneck analysis before
moving to real RDMA hardware.
