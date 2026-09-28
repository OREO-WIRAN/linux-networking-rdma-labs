# Lab 09 - Network Performance and Impairment Troubleshooting
## Objective
This lab demonstrates how network latency, jitter, and packet lossaffect network performance.
Linux `tc` (Traffic Control) and `netem` were used to simulatenetwork impairments between two Linux network namespaces.
## Lab Topology
hostA (ethA) <------ veth ------> hostB (ethB)
IP configuration:
- hostA: 10.80.0.1/24- hostB: 10.80.0.2/24
Both interfaces were configured with MTU 9000.
## Environment
- Ubuntu Linux on WSL2- Linux Network Namespaces- Virtual Ethernet (veth)- iproute2- ping- tc / netem
## Baseline Connectivity
Connectivity was verified before introducing network impairments.
```bashsudo ip netns exec hostA ping -c 4 10.80.0.2

The network operated normally with no packet loss and very low latency.
Add 50 ms Network DelayA 50 ms delay was introduced on hostA:
	sudo ip netns exec hostA tc qdisc add dev ethA root netem delay 50ms

The configuration was verified using:
	sudo ip netns exec hostA tc qdisc show dev ethA

Ping results showed an average RTT of approximately 50 ms.

This demonstrates how additional network delay directly affects latency.

Add Network Jitter
The configuration was changed to introduce variable delay:
	sudo ip netns exec hostA tc qdisc del dev ethA root
	sudo ip netns exec hostA tc qdisc add dev ethA root netem delay 50ms 10ms

The ping latency varied approximately between 41 ms and 59 ms.

Example result:
	rtt min/avg/max/mdev = 41.026/48.711/59.044/5.522 ms

This demonstrates network jitter, where packet latency is not constant.

Add Packet Loss
A 5% packet-loss condition was introduced together with delay and jitter:
	sudo ip netns exec hostA tc qdisc del dev ethA root
	sudo ip netns exec hostA tc qdisc add dev ethA root netem delay 50ms 10ms loss 5%

The test was performed using 100 ICMP packets:
	sudo ip netns exec hostA ping -c 100 10.80.0.2

Result:
	100 packets transmitted, 95 received, 5% packet loss
	rtt min/avg/max/mdev =40.347/50.091/60.067/6.193 ms

The missing ICMP sequence numbers also demonstrated packets being dropped.

Recovery Test
The simulated network impairment was removed:
	sudo ip netns exec hostA tc qdisc del dev ethA root

The qdisc configuration was checked:
	sudo ip netns exec hostA tc qdisc show dev ethA

Final connectivity test:
	sudo ip netns exec hostA ping -c 10 10.80.0.2

Result:
	10 packets transmitted, 10 received, 0% packet loss
	rtt min/avg/max/mdev =0.031/0.036/0.046/0.004 ms

The network successfully returned to normal operation.

Test Summary

Test        		Average RTT        Packet Loss
Baseline		Verylow			0%
50 ms Delay		~50.17 ms		0%
Delay + Jitter		~48.71 ms		0%
Delay + Jitter + Loss   ~50.09 ms		5%
Recovery		~0.036 ms		0%

Key Findings
-Latency represents the time required for packets to travel across a network.
-Jitter represents variation in packet latency.
-Packet loss occurs when packets fail to reach their destination.
-Linux tc and netem can simulate network performance problems.
-Baseline measurements are important before troubleshooting.
-Network recovery should always be verified after removing a fault.

Relevance to RDMA / RoCE
RDMA and RoCE environments are designed for high-throughput, low-latency communication.

Network latency, jitter, and packet loss can negatively affect distributed GPU and high-performance computing workloads.

Understanding how to measure and troubleshoot these conditions is an important foundation for 
RDMA, RoCE, GPU networking, and AI infrastructure engineering.
