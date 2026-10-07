# Lab 20 — RDMA Message Size, Queue Depth & Bandwidth-Delay Product

## Objective

Study the relationship between:

- Network bandwidth
- Latency
- Bandwidth-Delay Product (BDP)
- RDMA message size
- Queue Depth (QD)
- In-flight data
- Modeled throughput

This lab uses a simplified Python mathematical model.

The current WSL2 environment does not expose a real RDMA device.
Therefore, these results are not measurements from real RDMA or
NVIDIA ConnectX hardware.

---

## Core Concept

Bandwidth-Delay Product estimates how much data must be in flight to
fill a communication pipeline.

BDP is calculated as:

BDP = Bandwidth × Latency

A simplified relationship for this lab is:

In-Flight Data = Message Size × Queue Depth

To keep the modeled network pipeline full:

Message Size × Queue Depth ≈ BDP

Therefore:

Required QD ≈ BDP / Message Size

---

## Experiment 1 — 100 Gbit/s, 10 us Latency

Parameters:

- Bandwidth: 100 Gbit/s
- Latency: 10 us
- BDP: 125,000 bytes
- BDP: approximately 122 KiB

Selected results:

| Message Size | QD | In-Flight Bytes | Modeled Throughput |
|---:|---:|---:|---:|
| 256 B | 512 | 131,072 | 100 Gbit/s |
| 1,024 B | 128 | 131,072 | 100 Gbit/s |
| 4,096 B | 32 | 131,072 | 100 Gbit/s |
| 16,384 B | 8 | 131,072 | 100 Gbit/s |

The results show that different combinations of message size and Queue
Depth can provide approximately the same amount of in-flight data.

For example:

4 KiB × QD 32 = 128 KiB

16 KiB × QD 8 = 128 KiB

Both exceed the modeled BDP of approximately 122 KiB and therefore
reach the simulated 100 Gbit/s bandwidth ceiling.

---

## Message Size vs Queue Depth

With bandwidth and latency held constant:

Larger messages require fewer outstanding operations to provide the
same amount of in-flight data.

Smaller messages require more outstanding operations.

In the 10 us simulation:

| Message Size | First Tested QD Reaching 100 Gbit/s |
|---:|---:|
| 256 B | 512 |
| 1 KiB | 128 |
| 4 KiB | 32 |
| 16 KiB | 8 |

Increasing message size by 4x reduced the required tested Queue Depth
by approximately 4x.

---

## Experiment 2 — Increasing Latency

Latency was increased from:

10 us → 20 us

Bandwidth remained:

100 Gbit/s

The BDP therefore increased from:

125,000 bytes → 250,000 bytes

For a 4 KiB message:

At 10 us:

QD 32 produced 131,072 bytes of in-flight data and reached the modeled
100 Gbit/s ceiling.

At 20 us:

QD 32 still provided only 131,072 bytes of in-flight data.

Modeled throughput dropped to:

52.43 Gbit/s

Increasing QD to 64 provided:

262,144 bytes of in-flight data

and the simulation again reached:

100 Gbit/s

---

## Effect of Latency

Selected saturation points from the tested QD values:

| Message Size | 10 us | 20 us |
|---:|---:|---:|
| 256 B | QD 512 | QD 1024 |
| 1 KiB | QD 128 | QD 256 |
| 4 KiB | QD 32 | QD 64 |
| 16 KiB | QD 8 | QD 16 |

When latency doubled, BDP doubled.

With message size unchanged, approximately twice as much Queue Depth
was required in the tested values to provide enough in-flight data.

---

## Connection to Previous Labs

### Lab 16 — Message Size

Small application operations can create significant per-operation
overhead.

High link capacity alone does not guarantee high application
throughput.

### Lab 18 — Queue Depth

Queue Depth controls how many operations can remain outstanding.

Insufficient Queue Depth may prevent enough data from being in flight
to utilize the modeled link capacity.

### Lab 19 — Completion Processing

Increasing Queue Depth can increase the number of outstanding
operations and may increase completion-processing pressure.

Even when the BDP requirement is satisfied, another part of the data
path may become the bottleneck.

---

## Performance Engineering Interpretation

BDP helps answer:

"How much data should be in flight to keep the communication pipeline
busy?"

It does NOT answer:

"Which component is definitely the bottleneck?"

If Queue Depth is sufficient according to the BDP model but measured
throughput remains low, additional investigation is required.

Possible areas include:

- operation rate
- RNIC processing capacity
- CPU Work Request posting rate
- Completion Queue processing
- PCIe bandwidth and latency
- memory bandwidth
- NUMA placement
- protocol overhead
- application communication pattern

The correct approach is to measure the system and identify evidence
before assigning a bottleneck.

---

## Small-Message Consideration

Small messages may require very high operation rates to achieve high
bandwidth.

For example, ignoring protocol overhead, transferring 100 Gbit/s using
256-byte payloads would require approximately:

48.8 million operations per second

This means that satisfying the BDP requirement alone does not guarantee
that the RNIC, CPU, Completion Queue processing, or other parts of the
system can sustain the required operation rate.

---

## Lab Limitation

This experiment is a simplified mathematical simulation.

It does not model all real RDMA behavior, including:

- RNIC packet-processing limits
- PCIe behavior
- RDMA protocol overhead
- real Queue Pair limits
- Completion Queue limits
- CPU scheduling
- NUMA effects
- memory-system limits
- congestion
- hardware-specific behavior

The 100 Gbit/s value is a simulated bandwidth ceiling.

It is not a measurement of the physical network interface in the WSL2
environment.

---

## Key Takeaway

Bandwidth alone is not enough to understand communication performance.

The amount of data in flight depends on:

Bandwidth × Latency

while the application can influence in-flight data through:

Message Size × Queue Depth

BDP provides a useful model for estimating the concurrency required to
fill a communication pipeline, but real performance must still be
validated through measurement.
