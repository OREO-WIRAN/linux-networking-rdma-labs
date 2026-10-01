# Lab 16 — TCP Buffer Size and Throughput Analysis

## Objective

Investigate how application buffer size affects TCP throughput in a Linux network namespace environment.

## Environment

- WSL2
- Linux network namespaces
- hostA: 10.80.0.1
- hostB: 10.80.0.2
- iperf3
- Virtual Ethernet (veth) connection

> **Environment limitation:**

These measurements represent throughput through a virtual WSL2/Linux network-namespace path. They must not be interpreted as physical NIC line rate.

## Test Topology

hostA (10.80.0.1)
        |
        | veth
        |
hostB (10.80.0.2)

## Method

TCP throughput was measured using `iperf3` while changing the application buffer/block size.

Example:

```bash
sudo ip netns exec hostA iperf3 -c 10.80.0.2 -t 10 -l <SIZE>

## Experimental Results

| iperf3 block size (`-l`) | Observed throughput | Retransmissions | Observation |
|---|---:|---:|---|
| 1 byte | ~6.2–6.6 Mbit/s | 0 | Extremely low throughput |
| 128K | ~27.7 Gbit/s | 0 | Large throughput improvement |
| 1M | ~32.9–37.3 Gbit/s | 0 | Highest throughput observed in these runs |
| 4M | N/A | N/A | Rejected by iperf3; maximum allowed block size is 1 MiB |

## Initial Analysis

The experiment shows that application I/O size can have a major effect on
observed TCP throughput.

Using a very small block size creates much more per-operation overhead.
As the block size increases, more data can be processed per application
read/write operation, reducing relative overhead and allowing much higher
throughput.

However, increasing the block size does not create additional network
bandwidth. Performance eventually becomes limited by other parts of the
data path, such as CPU processing, memory movement, TCP behavior, and
the underlying virtual networking environment.

The `-l` option controls the iperf3 read/write buffer length. It should
not be interpreted as directly setting the TCP congestion window.

## Connection to RDMA and AI Infrastructure

This experiment demonstrates an important systems principle:

> High link capacity alone does not guarantee high application throughput.

When the application performs extremely small I/O operations, per-operation
overhead can dominate the data path. Increasing the amount of useful data
processed per operation can significantly improve efficiency.

This idea is relevant to high-performance AI networking.

Traditional TCP communication involves multiple software and kernel components,
including socket processing, protocol processing, memory movement, and CPU work.

RDMA is designed to reduce parts of this overhead by allowing applications to
use registered memory and RNIC-assisted data movement with reduced kernel
involvement in the data path.

However, RDMA does not remove every bottleneck.

Performance can still depend on factors such as:

- message size
- queue depth
- memory bandwidth
- PCIe bandwidth
- RNIC capabilities
- network congestion
- application communication patterns

For distributed AI workloads, poor communication efficiency can cause GPUs to
wait for data or synchronization even when the network has high nominal
bandwidth.

Therefore, AI infrastructure performance engineering requires measuring the
complete data path rather than assuming that link speed alone determines
application performance.
