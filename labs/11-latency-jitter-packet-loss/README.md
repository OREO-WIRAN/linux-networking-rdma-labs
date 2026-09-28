# Lab 11: Latency, Jitter, and Packet Loss

## Objective

Simulate network impairments using Linux `tc netem` and observe
their effects on latency, packet loss, TCP retransmissions, and throughput.

## Environment

- Linux / WSL2
- Network namespaces: hostA and hostB
- hostA: 10.80.0.1
- hostB: 10.80.0.2
- Tools: ping, tc, iperf3

## 1. Baseline Latency

Without network impairment, the network showed very low latency
and no packet loss.

Example result:

- Packet loss: 0%
- Average RTT: ~0.04 ms

## 2. Added 50 ms Latency

Command:

    sudo ip netns exec hostA tc qdisc add dev ethA root netem delay 50ms

Result:

- Average RTT increased to approximately 50 ms
- Packet loss remained 0%

This demonstrates how added network delay directly increases RTT.

## 3. Added Jitter

Network delay was configured with variation around 50 ms.

Observed result:

- Minimum RTT: 40.612 ms
- Average RTT: 50.111 ms
- Maximum RTT: 59.059 ms
- mdev: 5.225 ms
- Packet loss: 0%

The changing RTT values demonstrate network jitter.

## 4. Packet Loss

Configured packet loss:

    sudo ip netns exec hostA tc qdisc add dev ethA root netem loss 10%

Ping test:

- 50 packets transmitted
- 46 packets received
- Observed packet loss: 8%

The configured 10% loss is probabilistic, so the measured result
does not have to be exactly 10%.

## 5. TCP Performance Under Packet Loss

TCP performance was tested using iperf3 while packet loss was enabled.

Baseline performance before impairment:

- Throughput: ~24 Gbit/s
- TCP retransmissions: 0

Packet-loss test examples:

Run 1:

- Throughput: ~187 Mbit/s
- TCP retransmissions: 2855

Run 2:

- Throughput: ~77.6 Mbit/s
- TCP retransmissions: 1183

The results show that packet loss can cause TCP retransmissions and
trigger congestion-control behavior, significantly reducing and
destabilizing throughput.

## 6. Recovery

The network impairment was removed:

    sudo ip netns exec hostA tc qdisc del dev ethA root

Verification:

- 10 packets transmitted
- 10 packets received
- Packet loss: 0%
- Average RTT: 0.040 ms

The network returned to its normal baseline behavior.

## What I Learned

- Latency measures how long packets take to travel across the network.
- Jitter represents variation in packet latency.
- Packet loss means some packets fail to reach their destination.
- TCP retransmits lost data.
- Packet loss can trigger TCP congestion control and reduce throughput.
- Network bottlenecks can reduce the efficiency of distributed workloads.
- Measuring baseline performance before and after a change is important
  for troubleshooting network performance.
