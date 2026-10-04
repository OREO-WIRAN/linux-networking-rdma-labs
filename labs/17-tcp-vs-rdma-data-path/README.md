# Lab 17 — TCP Data Path vs RDMA Data Path

## Objective

Understand how CPU contention and per-operation overhead can affect
TCP application throughput, and connect these observations to the
motivation for RDMA.

This lab does NOT benchmark real RDMA hardware.

The current WSL2 environment does not expose an RDMA device, so the
experiments use TCP to study host-side performance behavior and then
compare the results conceptually with RDMA architecture.

---

## Environment

- WSL2 Ubuntu
- Linux network namespaces: hostA and hostB
- hostA: 10.80.0.1
- hostB: 10.80.0.2
- iperf3
- 8 logical CPUs visible to the environment

---

## TCP Data Path — Simplified

A simplified TCP application path is:

Application Buffer
        |
        v
Socket / System Call
        |
        v
Kernel TCP/IP Stack
        |
        v
NIC
        |
        v
Network
        |
        v
Remote NIC
        |
        v
Remote Kernel TCP/IP Stack
        |
        v
Remote Application

The exact number of memory copies and processing steps depends on the
implementation, kernel features, and offloads.

---

## RDMA Data Path — Simplified

After RDMA resources have been configured, a simplified steady-state
data path can look like:

Registered Memory
        |
        v
Work Request / Queue Pair
        |
        v
RNIC
        |
        v
Network
        |
        v
Remote RNIC
        |
        v
Remote Registered Memory

RDMA can reduce CPU involvement, kernel data-path processing, and
memory-copy overhead by using registered memory and RNIC offload.

RDMA does not eliminate CPU usage completely. CPU and kernel resources
are still involved in setup, resource management, posting work, and
completion handling depending on the application design.

---

## Experiment 1 — TCP Baseline

Command:

    sudo ip netns exec hostA iperf3 -c 10.80.0.2 -t 10

Observed result:

- Sender throughput: 26.9 Gbit/s
- Receiver throughput: 26.8 Gbit/s
- Retransmissions: 0

This is a WSL virtual-network measurement and must not be interpreted
as physical NIC performance.

---

## Experiment 2 — Pin iperf3 to CPU 0

Command:

    sudo ip netns exec hostA taskset -c 0 iperf3 -c 10.80.0.2 -t 10

Observed result:

- Throughput: approximately 25.8 Gbit/s
- Retransmissions: 1

Compared with the baseline, the throughput difference was relatively
small.

This result alone is not sufficient evidence that CPU was the
bottleneck.

Also, pinning the iperf3 process does not guarantee that every kernel
networking task or interrupt is processed on the same CPU.

---

## Experiment 3 — CPU Contention

A CPU-intensive process and the iperf3 client were intentionally
placed on CPU 0 at the same time.

CPU load:

    taskset -c 0 yes > /dev/null

While that process was still running, the TCP client was executed from
another terminal:

    sudo ip netns exec hostA taskset -c 0 iperf3 -c 10.80.0.2 -t 10

Observed result:

- Sender throughput: 13.7 Gbit/s
- Receiver throughput: 13.7 Gbit/s
- Retransmissions: 0

Compared with the 26.9 Gbit/s baseline, throughput decreased by
approximately 49%.

The important observation is:

    Throughput decreased significantly while retransmissions remained 0.

This demonstrates that low application throughput does not necessarily
require packet loss or TCP retransmissions.

CPU contention and host-side processing can also limit application
throughput.

---

## Connection to Lab 16

Lab 16 showed that application block size can have a major effect on
TCP throughput.

Very small blocks require many operations, causing per-operation
overhead to accumulate.

Larger blocks can amortize that overhead across more payload data.

Therefore:

    Link capacity != Application throughput

Application throughput may depend on:

- message or block size
- CPU availability
- memory movement
- system-call and software-processing overhead
- communication pattern
- network congestion

---

## Why RDMA Matters

RDMA is designed to reduce host-side communication overhead by using
registered memory, queue-based work requests, and RNIC offload.

In suitable workloads this can reduce:

- CPU involvement in payload movement
- kernel data-path processing
- memory-copy overhead
- communication latency

However:

    RDMA != zero overhead
    RDMA != unlimited bandwidth

Performance can still be limited by:

- physical network bandwidth
- RNIC capability
- PCIe bandwidth
- memory bandwidth
- queue depth
- congestion
- message size
- application synchronization
- CPU posting or polling overhead
- GPU communication and synchronization

---

## Bottleneck Shift

Optimizing one bottleneck can expose another.

Example:

    CPU bottleneck
          |
          | RDMA reduces CPU overhead
          v
    Network bandwidth becomes the next bottleneck

Therefore performance engineering should use measurements rather than
assuming where the bottleneck exists.

---

## Engineering Takeaways

1. Low throughput does not automatically mean packet loss.
2. CPU contention can reduce application throughput even when TCP
   retransmissions remain zero.
3. Small messages can suffer from high per-operation overhead.
4. RDMA reduces some CPU, kernel, and memory-copy overhead but does not
   eliminate every bottleneck.
5. Removing one bottleneck can expose the next bottleneck.
6. Measure first, then identify the limiting resource.

---

## Limitation

This lab used TCP inside WSL2 network namespaces.

It did not perform a real RDMA, RoCE, InfiniBand, or GPUDirect RDMA
benchmark.

The RDMA comparison in this lab is architectural and conceptual.
