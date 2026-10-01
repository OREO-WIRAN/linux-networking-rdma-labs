# Lab 15 — RoCE Fundamentals: Congestion, PFC, ECN, and Queueing

## Objective

This lab explores the networking concepts behind congestion management in RDMA over Converged Ethernet (RoCE).

The goals are to understand:

- How network congestion creates queueing delay
- Why high bandwidth does not guarantee low latency
- Why 0% packet loss does not necessarily mean good network performance
- The conceptual roles of PFC and ECN in RoCE networks
- How congestion control differs from flow control
- How to troubleshoot network performance using controlled experiments

> **Environment limitation:**
> This lab was performed using Linux network namespaces inside WSL2. The environment does not expose an RDMA/RoCE device,
  so the experiment below is a Linux queue/congestion simulation using `tc` and `netem`. It is **not** a real RoCE, PFC, ECN,
  or DCQCN hardware benchmark.

---

## Lab Topology

```text
hostA                                   hostB
10.80.0.1                              10.80.0.2
  ethA                                    ethB
    |                                      |
    +------------ virtual link ------------+
```

Traffic generation:

```text
hostA  ---- iperf3 / ICMP ---->  hostB
```

A controlled `100 Mbps` bottleneck was applied to `hostA` using Linux traffic control.

---

## RoCE Fundamentals

RDMA allows applications to transfer data between registered memory regions with reduced CPU/kernel involvement in the data path.

RoCE carries RDMA traffic over Ethernet.

Conceptually:

```text
Application
    |
    v
RDMA
    |
    v
RoCE
    |
    v
Ethernet Network
```

RoCEv2 uses UDP/IP transport encapsulation and can operate across Layer 3 networks.

RoCE is not TCP. Reliable Connected (RC) RDMA reliability is provided by the RDMA transport/RNIC rather than TCP.

---

## Congestion and Queueing

Congestion occurs when offered traffic exceeds the rate at which a bottleneck can forward traffic.

Example:

```text
Offered traffic
    150 Gbps
       |
       v
+---------------+
| Switch Queue  | -----> 100 Gbps bottleneck
+---------------+
       |
       +---- queue grows
             latency increases
```

A network can therefore have:

```text
High throughput
0% packet loss
High latency
```

at the same time.

This is why packet loss alone is not enough to determine whether a network is performing well.

---

## PFC — Priority Flow Control

Priority Flow Control (PFC) provides link-level flow control for selected Ethernet priorities.

When a queue associated with a priority becomes sufficiently congested, a device can send a PFC pause frame to its directly connected upstream neighbor.

Conceptually:

```text
Sender                         Switch
   |                              |
   | ------ RoCE traffic -------> |
   |                              | Queue pressure
   | <------ PFC PAUSE ---------- |
   |
   X  pause selected priority
```

PFC can help prevent buffer overflow and packet drops for selected traffic classes.

However, PFC does **not** create additional bandwidth and does not remove the underlying cause of congestion.

Poorly designed PFC behavior can contribute to:

- Pause propagation
- Congestion spreading
- Head-of-line blocking
- Potential deadlock scenarios

---

## ECN — Explicit Congestion Notification

ECN provides a way to signal congestion without waiting for packet loss.

Conceptually:

```text
Queue pressure
      |
      v
  ECN marking
      |
      v
Congestion feedback
      |
      v
Congestion-control mechanism
      |
      v
Adjust sending rate
```

ECN itself is a congestion signal. It does not directly reduce the sender's rate.

The congestion-control mechanism reacts to the feedback.

---

## PFC vs ECN

```text
PFC
 |
 +--> Pause selected priority temporarily
 |
 +--> Link-level flow control


ECN
 |
 +--> Mark congestion
 |
 +--> Generate congestion feedback
 |
 +--> Congestion control adjusts sending rate
```

The two mechanisms solve different problems and may coexist in a RoCE fabric.

---

## DCQCN Concept

DCQCN (Data Center Quantized Congestion Notification) is a congestion-control mechanism commonly associated with RoCEv2 deployments.

At a high level:

```text
Congestion
    |
    v
ECN marking
    |
    v
Congestion feedback / CNP
    |
    v
Congestion-control response
    |
    v
Sender rate adjustment
    |
    v
Reduced queue pressure
```

PFC and congestion control should not be treated as equivalent mechanisms.

PFC performs priority-based pause behavior, while congestion control attempts to regulate the offered traffic rate.

---

# Experiment

## 1. Create a 100 Mbps Bottleneck

The following queue discipline was applied to `hostA`:

```bash
sudo ip netns exec hostA tc qdisc add dev ethA root netem rate 100mbit limit 1000
```

Verification:

```bash
sudo ip netns exec hostA tc qdisc show dev ethA
```

The interface showed a `netem` queue with approximately `100 Mbit` rate limiting.

---

## 2. Throughput Test

`iperf3` was used to generate TCP traffic from `hostA` to `hostB`.

Example:

```bash
sudo ip netns exec hostA iperf3 -c 10.80.0.2
```

Parallel streams were then tested with:

```bash
sudo ip netns exec hostA iperf3 -c 10.80.0.2 -P 2
sudo ip netns exec hostA iperf3 -c 10.80.0.2 -P 4
sudo ip netns exec hostA iperf3 -c 10.80.0.2 -P 8
```

A longer congestion test used:

```bash
sudo ip netns exec hostA iperf3 -c 10.80.0.2 -P 16 -t 60
```

The receiver remained close to the configured bottleneck rate.

Approximate observed receiver throughput:

| Parallel Streams | Receiver Throughput |
|---:|---:|
| 1 | 99.2 Mbit/s |
| 2 | 99.2 Mbit/s |
| 4 | 99.0 Mbit/s |
| 8 | 99.0 Mbit/s |
| 16 | 99.1 Mbit/s |

Increasing the number of TCP streams did not multiply the physical/logical bottleneck capacity.

The flows had to share approximately the same `100 Mbps` bottleneck.

---

## 3. Idle Latency Baseline

Before generating sustained load:

```bash
sudo ip netns exec hostA ping -c 100 10.80.0.2
```

Observed result:

```text
100 packets transmitted
100 received
0% packet loss

rtt min/avg/max/mdev =
0.043 / 0.057 / 0.201 / 0.018 ms
```

Average latency:

```text
0.057 ms
```

---

## 4. Latency Under Load

A 16-stream `iperf3` test was run for 60 seconds:

```bash
sudo ip netns exec hostA iperf3 -c 10.80.0.2 -P 16 -t 60
```

At the same time:

```bash
sudo ip netns exec hostA ping -c 50 10.80.0.2
```

Observed throughput:

```text
Sender:   ~105 Mbit/s
Receiver: ~99.1 Mbit/s
TCP retransmissions: 0
```

Observed ping:

```text
50 packets transmitted
50 received
0% packet loss

rtt min/avg/max/mdev =
0.046 / 283.000 / 3747.298 / 895.457 ms
```

Despite:

```text
Packet loss = 0%
TCP retransmissions = 0
```

average latency increased from approximately:

```text
0.057 ms
```

to:

```text
283 ms
```

and maximum latency reached approximately:

```text
3.75 seconds
```

This demonstrates severe queueing delay under the artificial bottleneck.

---

## 5. Remove the Artificial Bottleneck

The injected queue discipline was removed:

```bash
sudo ip netns exec hostA tc qdisc del dev ethA root
```

Verification:

```bash
sudo ip netns exec hostA tc qdisc show dev ethA
```

Result:

```text
qdisc noqueue 0: root refcnt 2
```

---

## 6. Recovery Verification

Latency was measured again:

```bash
sudo ip netns exec hostA ping -c 50 10.80.0.2
```

Observed result:

```text
50 packets transmitted
50 received
0% packet loss

rtt min/avg/max/mdev =
0.032 / 0.061 / 0.357 / 0.043 ms
```

The average latency returned close to the original baseline.

---

# Results

| State | Avg RTT | Max RTT | Packet Loss |
|---|---:|---:|---:|
| Idle baseline | 0.057 ms | 0.201 ms | 0% |
| Under 100 Mbps bottleneck + load | 283.000 ms | 3747.298 ms | 0% |
| After bottleneck removal | 0.061 ms | 0.357 ms | 0% |

The experiment shows that extremely high queueing latency can occur even when no packet loss is observed.

---

# Engineering Analysis

The key observation was:

```text
0% packet loss != no congestion
```

During the loaded test, throughput remained close to the configured bottleneck capacity while latency increased dramatically.

This behavior is consistent with traffic accumulating in a queue rather than immediately being dropped.

The experiment also demonstrates why network troubleshooting should examine multiple metrics:

```text
Throughput
Latency
Packet loss
Retransmissions
Queue behavior
Congestion signals
```

In a real RoCE environment, additional telemetry may include ECN-related counters, congestion notifications,
PFC pause counters, and NIC/switch queue statistics.

No single metric should be used in isolation to declare the network healthy.

---

# Troubleshooting Workflow

This lab followed a controlled engineering workflow:

```text
Establish baseline
       |
       v
Inject controlled bottleneck
       |
       v
Generate load
       |
       v
Measure throughput + latency
       |
       v
Observe behavior
       |
       v
Form hypothesis
       |
       v
Remove fault
       |
       v
Re-measure
       |
       v
Verify recovery
```

A useful troubleshooting principle is:

> Don't guess where the bottleneck is — measure and find evidence.

---

# Important Limitation

This experiment does **not** demonstrate actual RoCE, PFC, ECN, or DCQCN packet behavior.

The test was performed with:

```text
WSL2
Linux network namespaces
veth interfaces
tc/netem
TCP iperf3 traffic
ICMP ping
```

The environment currently has no exposed RDMA device and no usable Soft-RoCE (`rdma_rxe`) module.

Therefore, the measured numbers should not be generalized to physical Ethernet/RoCE hardware.

The purpose of the experiment is to demonstrate the underlying queueing and congestion concepts that motivate congestion-management mechanisms in high-performance networks.

---

# Key Takeaways

1. High bandwidth does not guarantee low latency.
2. Zero packet loss does not guarantee a congestion-free network.
3. Queueing can produce severe latency even while throughput remains high.
4. PFC provides priority-based flow control but does not create bandwidth or eliminate the root cause of congestion.
5. ECN provides congestion signaling that congestion-control mechanisms can react to.
6. PFC and ECN have different roles and can coexist.
7. Performance troubleshooting requires measurements before, during, and after a controlled change.
8. Recovery should always be verified rather than assumed.
