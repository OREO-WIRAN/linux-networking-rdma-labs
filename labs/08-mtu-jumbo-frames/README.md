# Lab 08 — MTU & Jumbo Frames Troubleshooting
## Objective
This lab demonstrates how MTU (Maximum Transmission Unit) affects network communication and how MTU mismatch can cause packet transmission failures.
The lab uses Linux network namespaces to simulate two hosts connected through a virtual Ethernet (veth) pair.
## Lab Topology
hostA (ethA) <------ veth ------> hostB (ethB)
IP Configuration:
- hostA: 10.80.0.1/24- hostB: 10.80.0.2/24
## Environment
- Ubuntu Linux on WSL2- Linux Network Namespaces- Virtual Ethernet (veth)- iproute2- ping
## Baseline Test — MTU 1500
Both interfaces were initially configured with MTU 1500.
A normal connectivity test was successful:
```bashsudo ip netns exec hostA ping -c 4 10.80.0.2
Result:
4 packets transmitted, 4 received, 0% packet loss

To test the MTU boundary without IP fragmentation:
	sudo ip netns exec hostA ping -c 4 -M do -s 1472 10.80.0.2

The test succeeded.
1472 bytes ICMP payload + 28 bytes IP/ICMP headers = 1500 bytes.

Increasing the payload to 1473 bytes caused:
	ping: sendmsg: Message too long

This demonstrated the MTU 1500 boundary.

Jumbo Frame Configuration
Both interfaces were changed to MTU 9000:
	sudo ip netns exec hostA ip link set dev ethA mtu 9000
	sudo ip netns exec hostB ip link set dev ethB mtu 9000

The configuration was verified using:
	sudo ip netns exec hostA ip link show ethA
	sudo ip netns exec hostB ip link show ethB

Jumbo Frame Test
A jumbo-frame ping was tested using:
	sudo ip netns exec hostA ping -c 4 -M do -s 8972 10.80.0.2

8972 bytes payload + 28 bytes IP/ICMP headers = 9000 bytes.

Result:
	4 packets transmitted, 4 received, 0% packet loss

A payload of 8973 bytes exceeded the MTU and failed with:
	ping: sendmsg: Message too long

Troubleshooting Scenario — MTU Mismatch
To simulate a network configuration problem, hostB was changed back to MTU 1500 while hostA remained at MTU 9000.

Configuration:
	hostA ethA MTU = 9000
	hostB ethB MTU = 1500

A standard MTU-sized packet still succeeded:
	sudo ip netns exec hostA ping -c 4 -M do -s 1472 10.80.0.2

However, the jumbo-frame test failed.
	sudo ip netns exec hostA ping -c 4 -M do -s 8972 10.80.0.2

This produced packet transmission errors and 100% packet loss.

Root Cause
The failure was caused by an MTU mismatch between the two endpoints.
hostA was configured for MTU 9000 while hostB was configured for MTU 1500.
Large packets could therefore not traverse the complete network path.

Resolution
The MTU on hostB was restored to 9000:
	sudo ip netns exec hostB ip link set dev ethB mtu 9000

Both endpoints were then verified:
	sudo ip netns exec hostA ip link show ethA 
	sudo ip netns exec hostB ip link show ethB

Final configuration:
	hostA ethA MTU = 9000
	hostB ethB MTU = 9000

VerificationThe jumbo-frame test was repeated:
	sudo ip netns exec hostA ping -c 4 -M do -s 8972 10.80.0.2

Result:
	4 packets transmitted, 4 received, 0% packet loss

The issue was successfully resolved.

Key Findings
-MTU defines the maximum packet size that can be transmitted on an interface.
-Standard Ethernet commonly uses MTU 1500.
-Jumbo frames can use a larger MTU such as 9000.ping -M do is useful for testing packet size without fragmentation.
-MTU must be configured consistently across the communication path.
-MTU mismatch can allow small packets to work while larger packets fail.
-MTU verification is an important troubleshooting step for high-performance networks.

Relevance to RDMA / RoCE

High-performance networks used for RDMA and RoCE require careful network configuration.

MTU consistency is important because RDMA workloads can transfer large amounts of data at high throughput. 
Incorrect MTU configuration can cause packet loss, degraded performance, or connectivity problems.

Understanding MTU and jumbo-frame troubleshooting is therefore an important foundation for RDMA, RoCE, 
GPU networking, and AI infrastructure engineering.
