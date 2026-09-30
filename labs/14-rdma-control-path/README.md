# Lab 14 — RDMA Control Path, QP Setup, and Network Loss Analysis
## Objective
This lab studies how an RDMA communication path is prepared beforepayload data can be transferred.

Topics:
- Control Path vs Data Path
- Memory Region information exchange
- Remote address and rkey
- Memory permissions and boundaries
- Queue Pair (QP) information
- QP state transitions
- Queue Pair Number (QPN)
- Packet Sequence Number (PSN)
- Transport reliability concepts
- Packet loss and throughput degradation
- Performance troubleshooting methodology

> Note:
> The current WSL2 environment does not expose a real RDMA device.
> Therefore, the packet-loss experiment in this lab uses TCP,
> Linux network namespaces, iperf3, and netem.
> The measured TCP results must not be interpreted as RoCE/RDMA
> benchmark results.
---

## 1. Control Path vs Data Path
Before an RDMA operation can move application payload, both nodesmust prepare the communication environment.

Conceptually:
    
	CONTROL PATH
    
	Node A                         Node B       
	|                             |       
	|  Exchange connection info  |       
	|<--------------------------->|       
	|                             |       
	|  Exchange MR information   |       
	|<--------------------------->|       
	|                             |

After setup:
    
	DATA PATH
    
	Node A                         Node B
    
	Gradient       
	|       
	|       RDMA WRITE       
	+---------------------------> MR

The control path prepares the communication.
The data path moves the actual workload payload.

---

## 2. Remote Memory Information

Suppose Node B registers a Memory Region:
    
	Address    = 0xABCDEF    
	Length     = 1 GB    
	rkey       = 7391    
	Permission = REMOTE_WRITE

For Node A to perform an appropriate remote operation, it needsthe required remote memory information.
The RDMA NIC does not automatically discover the remote MR addressand rkey.

This information must be exchanged as part of application orconnection setup.

---

## 3. IP Address vs Memory Address

An IP address and an MR address are different concepts.

Example:
  
	Node B IP Address    10.80.0.2

This identifies a network endpoint in the IP networking context.

A registered memory address such as:
    
	0xABCDEF

identifies a memory location associated with the registered region.

Therefore:
    
	IP address != MR address
---
## 4. rkey
The rkey is used by the RDMA hardware as part of validating remoteaccess to a registered Memory Region.

Example:
    
	Remote Address = correct    
	rkey           = incorrect

The remote access should not be accepted merely because the memoryaddress is known.

Important:
    
	rkey is not a human password.

It is part of the RDMA memory protection mechanism.

---

## 5. Permission Checking
A correct rkey does not mean that every operation is permitted.

Example:
    
	MR Permission = REMOTE_READ only

Node A attempts:
    
	RDMA WRITE
Even with the correct address and rkey, the WRITE is not permittedbecause the MR was not registered for remote write access.

Therefore remote access depends on multiple conditions.

Conceptually:
    
	Address / Range          
		+        
		rkey          
		+      
		Permission          
		+    
	Valid communication state          
		|          
		v    
	Remote operation

---

## 6. Memory Boundary
An RDMA operation must remain within the permitted registeredmemory range.

Example:
    
	MR Address = 0x1000    
	Length     = 1024 bytes

Conceptually:
       
	Registered Memory Region       
	<----------------------->
    
	0x1000                  0x13FF       
	|                       |       
	+-----------------------+       
	|     Allowed Memory    |       
	+-----------------------+

An operation extending beyond the registered region should not beaccepted simply because its rkey is correct.

Therefore:
    
	Correct rkey        
	    !=    
	Unlimited memory access
---
## 7. Control Information Exchange
The nodes need a mechanism to exchange setup information beforeusing the RDMA data path.
A simple application design could use a TCP socket as anout-of-band control channel.

For example:
    
	Node A                         Node B       
	|                             |       
	|       TCP control           |       
	|<--------------------------->|       
	|                             |       
	|  MR address / rkey          |       
	|<--------------------------->|       
	|                             |       
	|  QP / transport info        |       
	|<--------------------------->|

After setup, the application can use the RDMA data path forhigh-performance payload movement.

TCP is only one possible example of a control mechanism.

RDMA connection-management mechanisms can also be used.

Therefore:
    
	RDMA does not always require TCP for setup.

---

## 8. Control Payload vs Application Payload

Control information is typically relatively small.

Examples:
    
	Remote address    
	rkey    
	QP information    
	Transport parameters

The application payload may be much larger.

For an AI workload:
    
	Control metadata        -> small
	Gradient        -> potentially very large

This separation allows the system to use an appropriate mechanismfor setup while using a high-performance data path for largepayload movement.
---

## 9. Queue Pair State

For a Reliable Connected (RC) Queue Pair, important states include:
    
	RESET      
	|      
	v    
	INIT      
	|      
	v    
	RTR      
	|      
	v    
	RTS

Where:
    
	RESET = initial/reset state
    
	INIT  = QP is being initialized/configured

	RTR   = Ready To Receive
    
	RTS   = Ready To Send

A QP in INIT is not yet ready to send normal RDMA work as an RTS QP.

Therefore, knowing the remote address and rkey alone is not enough.

The communication path must also be properly configured.

---

## 10. QPN — Queue Pair Number

QPN stands for:
    
	Queue Pair Number

It identifies a Queue Pair within the relevant RDMA transportcontext.

A device may have many Queue Pairs:
    
	QP 100 -> AI job A    
	QP 101 -> AI job B    
	QP 102 -> Storage communication    
	QP 103 -> Another connection

MR information and QP information serve different purposes.

Mental model:
    
	MR information        -> Which memory?
    
	QP / connection information        -> Which communication context?

An rkey does not identify the remote QP.

---

## 11. PSN — Packet Sequence Number

PSN stands for:
    
	Packet Sequence Number

For transports such as RC, sequence information participates inreliable and ordered transport behavior.

Conceptually:
    
	PSN 500    
	PSN 501    
	PSN 502    
	PSN 503

If the expected sequence instead appears as:
    
	PSN 500    
	PSN 501    
	PSN 503

then PSN 502 is missing from the expected sequence.

This is a transport/packet-sequence concern.

It is different from an rkey problem.

Mental model:
    
	PSN      -> packet sequence
    
	rkey      -> remote memory access authorization
    
	QPN      -> Queue Pair / communication context
    
	Remote Address      -> memory location

---

## 12. Troubleshooting by Layer

If an RDMA WRITE fails, a performance or infrastructure engineershould not immediately assume a single cause.

Possible checks include:
    
	Is the QP in the correct state?
    
	Is the connection/transport configured correctly?
    
	Is the remote address correct?
    
	Is the rkey correct?
    
	Does the MR permit the requested operation?
    
	Is the access inside the registered memory range?
    
	Are there network errors or transport problems?

The goal is to isolate the layer responsible for the failure.
---

# Experiment — Packet Loss and Throughput

## 13. Test Environment

This experiment uses:
- WSL2
- Linux network namespaces
- hostA
- hostB
- iperf3
- Linux tc/netem
- TCP

Network:
    
	hostA    10.80.0.1
    
	hostB    10.80.0.2

This experiment is NOT a real RoCE benchmark.

It is used to demonstrate how network impairment can affecttransport performance.

---

## 14. Baseline

iperf3 server:
    
	sudo ip netns exec hostB iperf3 -s

iperf3 client:
    
	sudo ip netns exec hostA iperf3 -c 10.80.0.2

Measured baseline:
    
	Transfer = 27.3 GBytes    
	Bitrate  = 23.5 Gbit/s    
	Retr     = 0

This represents the reference measurement for this experiment.

---

## 15. Inject 1% Packet Loss

Packet loss was introduced on hostA:
    
	sudo ip netns exec hostA tc qdisc add dev ethA root netem loss 1%

The configuration was verified with:
    
	sudo ip netns exec hostA tc qdisc show dev ethA

Measured result:
    
	Transfer = 15.2 GBytes    
	Bitrate  = 13.1 Gbit/s    
	Retr     = 19,300

Compared with baseline:
    
		Throughput:    
		23.5 Gbit/s          
		|          
		v    
		13.1 Gbit/s

This is approximately a 44% throughput reduction.

The configured packet loss was only 1%, but application throughputdecreased by much more than 1%.

---

## 16. Test with 0.1% Packet Loss

The existing qdisc was changed:
    
	sudo ip netns exec hostA tc qdisc change dev ethA root netem loss 0.1%

Verification:
    
	sudo ip netns exec hostA tc qdisc show dev ethA

Measured result:
    
	Transfer = 25.4 GBytes    
	Bitrate  = 21.8 Gbit/s    
	Retr     = 3,159

Compared with baseline:
    
	23.5 Gbit/s          
	|          
	v    
	21.8 Gbit/s

This is approximately a 7% throughput reduction in this run.

Again:
    
	Packet loss percentage        
		!=    
	Throughput reduction percentage

The relationship is not necessarily linear.

---

## 17. TCP Retransmissions

Measured retransmissions:
    
	0% loss        Retr = 0
	
	0.1% loss      Retr = 3,159
    
	1% loss        Retr = 19,300

The iperf3 Retr value represents TCP retransmissions.
It must not be interpreted directly as the number of packetsdropped by netem.
TCP reacts to loss through mechanisms including retransmissionand congestion control.
Therefore a small amount of packet loss can produce a much largerperformance effect than simply subtracting 
the loss percentagefrom the available throughput.

---

## 18. Congestion Window

During the impaired tests, the TCP congestion window (Cwnd)changed significantly.
This demonstrates that the transport reacts dynamically tonetwork conditions.
The link itself was not configured with a bandwidth limit duringthis experiment.
Instead, transport behavior affected how efficiently theavailable capacity could be used.

Therefore:
    
	High link bandwidth        
		!=    
	Guaranteed high application throughput

---

## 19. Recovery Test

The artificial packet loss was removed:
    
	sudo ip netns exec hostA tc qdisc del dev ethA root

Verification:
    
	sudo ip netns exec hostA tc qdisc show dev ethA
Result:
    
	qdisc noqueue 0: root refcnt 2

iperf3 was executed again.

Measured recovery:
    
	Transfer = 25.5 GBytes    
	Bitrate  = 21.9 Gbit/s    
	Retr     = 1

The throughput did not return to exactly 23.5 Gbit/s, becausebenchmark results can vary between runs.

However, retransmissions decreased from:
    
	19,300        
	|        
	v        
	1

and throughput recovered substantially from the 1% loss result.

This supports the conclusion that the injected packet loss wasa major cause of the observed degradation in this experiment.

---

## 20. Experiment Summary

| Condition | Bitrate | TCP Retr |
|---|---:|---:|
| Baseline — 0% artificial loss | 23.5 Gbit/s | 0 |
| 0.1% artificial loss | 21.8 Gbit/s | 3,159 |
| 1% artificial loss | 13.1 Gbit/s | 19,300 |
| Recovery — artificial loss removed | 21.9 Gbit/s | 1 |

Important:

These measurements are specific to this WSL2 
TCP/network-namespace

experiment.
They must not be generalized into claims such as:
    
	"1% packet loss causes a 44% reduction in RoCE performance."

No real RDMA or RoCE traffic was measured here.
---

## 21. Performance Troubleshooting Method

This lab demonstrates a useful troubleshooting workflow:
    
	1. Establish baseline              
		|              
		v    
	2. Introduce a controlled change              
		|              
		v    
	3. Observe degradation              
		|              
		v    
	4. Collect metrics              
		|              
		v    
	5. Form and test a hypothesis              
		|              
		v    
	6. Remove the change              
		|              
		v    
	7. Verify recovery

This helps distinguish evidence from assumptions.

---

## 22. Connection to AI / GPU Infrastructure

Slow AI training does not automatically mean that the GPU itselfis the bottleneck.

An AI workload can be affected by:

- GPU compute
- CPU processing
- Memory bandwidth
- PCIe
- Storage / data loading
- Network bandwidth
- Network latency
- Packet loss or errors
- RDMA communication
- Completion processing
- Synchronization between GPUs or nodes

For example:
    
	Network impairment           
		|           
		v    
	Communication slows           
		|           
		v    
	Dependent GPU work waits           
		|           
		v    
	Training iteration time increases

A low GPU utilization metric can therefore be a symptom ratherthan the root cause.

A performance engineer should ask:
    
	"What is the workload waiting for?"

and then collect evidence across the system.

---

## 23. Key Lessons
1. RDMA has both control/setup concerns and a data path.
2. Remote address and rkey must be known before appropriate   
   one-sided remote memory access can occur.
3. Correct rkey alone is not enough.
4. MR permissions and memory boundaries must also be valid.
5. MR information and QP information have different purposes.
6. RC QPs transition through states such as:
	RESET -> INIT -> RTR -> RTS
7. QPN identifies a Queue Pair communication context.
8. PSN relates to packet sequence handling.
9. rkey relates to remote registered-memory access authorization.
10. Small packet-loss percentages can have disproportionately    
   large effects on transport/application performance.
11. Throughput degradation should be investigated with multiple    
   metrics rather than assumed from one number.
12. Removing a controlled fault and verifying recovery provides    
   useful evidence about root cause.
13. GPU performance problems can originate outside the GPU.
14. Performance engineering requires measuring the entire system    
   and identifying what the workload is waiting for.

---

## Mental Model
    
	Control Path        		= Prepare communication
    
	Data Path           		= Move workload payload
    
	QPN                 		= Which QP / communication context?
    
	PSN                 		= Which packet sequence?
    
	Remote Address      		= Which memory location?
    
	rkey                		= Is this remote memory access authorized?
    
	MR Permission        		= Is this operation allowed?
    
	CQ                   	        = What work completed?
    
	Performance Engineering         = Measure, isolate, test, and verify
