# Lab 04 - MTU and Packet Size

## Objective

Understand Ethernet MTU, IP packet size, and how Linux handles packets that exceed the interface MTU when fragmentation is disabled.
This lab demonstrates the packet-size boundary of an interface configured with an MTU of 1500 bytes.

## Environment
-Ubuntu Linux on WSL2
-Interface: eth0
-Interface MTU: 1500 bytes
-Test destination: 172.24.160.1
## Check Interface MTU
Command:
```bash
ip link show eth0

The interface reported:
mtu 1500

This means the maximum IPv4 packet size transmitted without fragmentation is 1500 bytes.

Packet Size Calculation
For an IPv4 ICMP echo request:
-IPv4 header = 20 bytes
-ICMP header = 8 bytes
-ICMP payload = variable

Therefore:
1472 + 20 + 8 = 1500 bytes
1473 + 20 + 8 = 1501 bytes

Test 1 - 1500-byte Packet
Command:
ping -c 2 -M do -s 1472 172.24.160.1

Result:
2 packets transmitted, 2 received, 0% packet loss
The packet was successfully transmitted because its total IPv4 packet size was exactly 1500 bytes.

Test 2 - Packet Exceeding MTU
Command:
ping -c 2 -M do -s 1473 172.24.160.1

Result:
ping: sendmsg: Message too long

The total packet size was 1501 bytes,which exceeded the interface MTU.
Because -M do disables IPv4 fragmentation,Linux refused to transmit the oversized packet.

What I Learned
-MTU defines the maximum Layer 3 packet size that can be transmitted without fragmentation.
-IPv4 and ICMP headers must be included when calculating the total packet size.
-A 1472-byte ICMP payload produces a 1500-byte IPv4 packet.
-A 1473-byte ICMP payload produces a 1501-byte IPv4 packet and exceeds an MTU of 1500.
-ping -M do is useful for testing Path MTU because fragmentation is disabled.
-MTU configuration must be consistent across a network path to avoid connectivity and performance problems.

Relevance to RDMA and RoCE
RDMA and RoCE environments require careful network configuration for predictable high-performance communication.
MTU and jumbo-frame configuration become especially important in high-bandwidth networks used by GPU and AI clusters.
Understanding packet size and MTU is therefore a networking foundation for later labs covering:
-Jumbo Frames
-RoCE
-RDMA
-NVIDIA ConnectX networking
-GPU cluster networking
Result
Successfully identified the interface MTU and experimentally verified the MTU boundary using ICMP packets with IPv4 fragmentation disabled.

