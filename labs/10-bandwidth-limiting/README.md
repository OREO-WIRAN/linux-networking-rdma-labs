# Lab 10: Bandwidth Limiting with Linux tc and iperf3
## Objective
Test network bandwidth between two Linux network namespaces and observehow traffic shaping affects TCP throughput.
## Lab Environment
- Ubuntu on WSL2- Linux Network Namespaces- hostA: 10.80.0.1- hostB: 10.80.0.2- iperf3- Linux Traffic Control (tc)
## Baseline Test
Without bandwidth limiting:
- Throughput: approximately 24 Gbit/s- TCP retransmissions: 0
## 125 Mbit/s Bandwidth Limit
Traffic control was configured using TBF (Token Bucket Filter).
Measured with iperf3:
- Sender: approximately 126 Mbit/s- Receiver: approximately 125 Mbit/s- TCP retransmissions: 0
## 1 Gbit/s Bandwidth Limit
Traffic control was configured with:
```bash
sudo ip netns exec hostA tc qdisc add dev ethA root tbf rate 1000000kbit burst 1Mb latency 50ms

Verification:
	sudo ip netns exec hostA tc qdisc show dev ethA

Result:
rate 1Gbit burst 1000000b lat 50ms

iperf3 Test:
	sudo ip netns exec hostA iperf3 -c 10.80.0.2

Measured result:
-Transfer: 1.16 GBytes
-Sender throughput: 994 Mbit/s
-Receiver throughput: 993 Mbit/s
-TCP retransmissions: 0

Results

Test			Configured Rate			Measured Throughput
Baseline		Unlimited			~24 Gbit/s
TBF Test 1		125 Mbit/s			~125 Mbit/s
TBF Test 2		1 Gbit/s			~993-994 Mbit/s

What I Learned
This lab demonstrates the difference between available network capacity and administratively controlled bandwidth.

Linux Traffic Control (tc) can shape network traffic using a Token Bucket Filter (tbf), while iperf3 
can be used to measure the actual TCP throughput.

The experiment showed that changing the configured bandwidth limit produced corresponding changes in measured throughput.
