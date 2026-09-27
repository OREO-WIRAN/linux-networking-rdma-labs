# LAb 05 - Path MTU Discovery

## Objective

The lab demonstrates how to identify and verify the Path MTU
between a Linux host and a network destination.

The goal is to understand how packet size, MTU, and the 
Don't Fragment(DF) behavior affect network communication.

## Environment
- Ubuntu Linux on WSL2
- Interface: eth0
- Local IP: 172.24.160.77
- Default gateway: 172.24.160.1
- Interface MTU: 1500 bytes

## Route Verification

The routing table was:
default via 172.24.160.1 dev eth0
The route to an external destination was also checked using:
ip route get 1.1.1.1
This confirmed that traffic uses eth0 through the default gateway.

## Connectivity Testing
An external destination (1.1.1.1.) did not respond to ICMP ping from this WSL2 environment.
However, the default gateway 172.24.160.1 responded successfully.

Therefore,the gateway was used as the test destination for the MTU experiment.

## MTU Test
For IPv4 ICMP:
IPv4 header = 20 bytes
ICMP header = 8 bytes
Therefore:
1472 + 20 + 8 = 1500 bytes
1473 + 20 + 8 = 1501 bytes

###Test 1 - 1500-bytes IPv4 Packet
command:
ping -c 2 -M do -s 1472 172.24.160.1
Result:
2 packets transmitted, 2 received, 0% packet loss

The packet was transmitted successfully because the total IPv4 packet size was 1500 bytes.

###Test 2 - Packet Larger Than MTU 
Command:
ping -c 2 -M do -s 1473 172.24.160.1
Result:
ping: sendmsg: Message too long

The packet could not be transmitted because the total IPv4 packet size was 1501 bytes,
exceeding the MTU of 1500 bytes while fragmentation was disabled.

## Relevance to RDMA and RoCE

Path MTU is important in high-performance networking.
RDMA and RoCE environments require consistent MTU configuration across the network path.

MTU mismatches can cause packet loss, connectivity problems, or reduced network performance.

Understanding Path MTU Discovery is therefore an important foundation for:
-Jumbo Frames
-RoCE
-RDMA
-NVDIA Connectx networking
-GPU cluster networking

## Result
Successfully verified a 1500-byte MTU boundary using ICMP packets with IPv4 Fragmentation disabled.
A 1500-byte IPv4 packet succeeded, while a 1501-byte packet faild with "Message too long". 
