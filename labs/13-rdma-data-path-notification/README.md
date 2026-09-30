# Lab 13 — RDMA Data Path, Notification, and Completion Polling
## Objective
This lab studies the RDMA data path and how an application learns thatremote data is ready.
Topics:
- RDMA WRITE
- RDMA WRITE WITH IMMEDIATE
- Memory Region (MR)
- Receive Queue (RQ)
- Completion Queue (CQ)
- Work Completion
- Immediate Data
- CQ Polling
- Busy Polling vs Event-Driven Completion
- CPU utilization and latency trade-offs
- Connection to GPU / AI infrastructure bottlenecks
> Note: This is a conceptual architecture lab.
> The current WSL2 environment does not expose an RDMA device,
> so no real RDMA verbs benchmark is performed in this lab.
---
## 1. RDMA WRITE
With a normal RDMA WRITE, the initiator writes data directly intoa permitted Memory Region on the remote node.

Example:

Node A:
    
	Gradient Data         
		|         
		| RDMA WRITE         
		v
Node B:
    
	Memory Region (MR)    
	+------------------+    
	| Gradient Data    |    
	+------------------+

The payload is placed into the remote MR.
An important point is that a normal RDMA WRITE does not by itself produce a receive completion that tells the remote application:
    
	"New data is ready."
Therefore, data movement and application notification are separateconcepts.
---
## 2. Data Movement vs Notification

### Data Movement

Data movement answers:

	Where did the payload go?

For RDMA WRITE:

	Payload -> Remote Memory Region
Example:
    
	"GPU Gradient Data"            
		|            
		v       
		Remote MR

### Notification

Notification answers:
    
	How does the remote application know that something happened    
    	or that data is ready according to the application protocol?

The application needs a mechanism to distinguish between:
    
	Data exists in memory
and:
    
	The application knows that the data is ready to use
These are not the same thing.

---

## 3. RDMA WRITE WITH IMMEDIATE

RDMA WRITE WITH IMMEDIATE combines:
1. RDMA WRITE data movement
2. A small immediate value reported with a receive-side completion

Example:

Node A:
    
	Payload: "Gradient"    
	Immediate Data: 7

Data path:
    
		Gradient       
		|       
		| RDMA WRITE       
		v
		Node B MR:
		+----------------+    
		| Gradient       |    
		+----------------+

Completion information:
    
	Receive-side Work Completion    
	Immediate Data = 7

The immediate value is not the payload.
It can be application-defined metadata.
For example:

	Immediate = 7

could mean:

	"Buffer 7 is ready"

depending on the application's protocol.

---

## 4. MR, RQ, and CQ Have Different Jobs
### MR — Memory Region
	MR contains registered memory that RDMA operations are permittedto access.
In this example:
    
	MR    
	+----------------+    
	| Gradient       |    
	+----------------+

The Gradient is the real payload.
The application reads the actual Gradient from the memory locationused by the protocol, not from the Completion Queue.

---

### RQ — Receive Queue
The Receive Queue contains posted Receive Work Requests.
For RDMA WRITE WITH IMMEDIATE, the remote side must have anappropriate Receive Work Request 
posted so that the receive-sidecompletion can be generated.

Important:

	RQ != Notification    
	RQ != Completion Queue

RQ prepares receive work.

---

### CQ — Completion Queue

The Completion Queue contains Work Completions.

A completion may contain information such as:
- Operation status- Operation type- Immediate Data when applicable

Example:
    
	CQ    
	+----------------------+    
	| Work Completion      |    
	| Status = SUCCESS     |    
	| Immediate = 7        |    
	+----------------------+
CQ does not contain the Gradient payload.
The Gradient remains in the target memory region.

A useful mental model:
    
	MR = Where the data is    
	CQ = What happened
---
## 5. WRITE vs WRITE WITH IMMEDIATE vs SEND

| Operation | Payload Destination | Remote Posted Receive Required | Remote Receive Completion |
|---|---|---:|---:|
| RDMA WRITE | Remote MR | No | No receive completion from ordinary WRITE || RDMA WRITE WITH IMMEDIATE | Remote MR | Yes 
| Yes || SEND | Posted receive buffer | Yes | Yes |

This distinction is important.

With WRITE WITH IMMEDIATE, the posted Receive Work Request supportsthe receive-side completion.

The RDMA WRITE payload itself still goes to the target MR specifiedby the remote address and rkey.
---

## 6. CQ Polling
Polling means that the application checks the Completion Queue tosee whether a Work Completion is available.

Conceptually:
    
	Application / CPU            
		|            
		| poll            
		v           
		CQ       
	[ no completion ]

The CPU may check again:

	poll -> empty    
	poll -> empty    
	poll -> empty    
	poll -> completion found

When a completion is found:
    
	CQ    
	+----------------------+    
	| Work Completion      |    
	| Immediate = 7        |    
	+----------------------+             
		|             
		v       
		Application

The application can interpret the completion and then access thecorresponding payload in memory.

---

## 7. Busy Polling

A simplified busy-polling loop looks conceptually like:

	while (true) {        
	    check_CQ();    
	}
The CPU continuously checks the CQ.

Advantages:
- Very fast completion detection
- Useful for latency-sensitive workloads
- Can reduce wake-up delay

Trade-off:
- Consumes CPU cycles
- A CPU core may spend significant time polling even when the CQ is empty

Therefore:
    
	Lower latency         
	     vs    
	Higher CPU utilization

is an important performance trade-off.

---

## 8. Event-Driven Completion
Instead of continuously polling, an application can use anevent-driven approach.

Conceptually:
    
	CPU waits / performs other work              
		|        
	Completion arrives              
		|              
		v       
	Completion Event              
		|              
		v      
	Application wakes              
		|              
		v         
	   Process CQ

This can improve CPU efficiency.
However, event handling and wake-up may introduce additionaloverhead or latency compared with aggressive busy polling.

This does not mean event-driven processing always has "high latency."

The correct interpretation is:
    
	Busy polling        
	-> potentially lower latency        
	-> higher CPU usage
    
	Event-driven        
	-> potentially better CPU efficiency        
	-> may add wake-up/event overhead
The correct choice depends on workload requirements.
---

## 9. RDMA Does Not Mean Zero CPU Usage

RDMA reduces CPU and kernel involvement in the data movement path.

However, the CPU still has responsibilities such as:
- Application control logic
- Queue Pair setup
- Memory registration
- Posting Work Requests
- Completion processing
- CQ polling
- Error handling

Therefore:

    RDMA reduces CPU involvement

does not mean:

    RDMA uses no CPU

These are different statements.

---

## 10. CPU Utilization as a Performance Metric

High CPU utilization does not automatically mean that the systemhas a bottleneck.

For example:

	CPU Core 0 -> Application    
	CPU Core 1 -> Application    
	CPU Core 2 -> Busy CQ Polling    
	CPU Core 3 -> Other Work

If Core 2 is intentionally dedicated to low-latency CQ polling,
high utilization on that core may be an expected design trade-off.

A performance engineer should ask:
    
	Why is CPU utilization high?
and:
    
	Is this utilization expected by the system design?

rather than immediately concluding:

	High CPU = Problem

---

## 11. Connection to GPU and AI Infrastructure

In distributed AI training, GPU computation and networkcommunication must work together.

Conceptually:

	GPU     
	|     
	| Compute Gradient     
	v    
	GPU Memory     
	|     
	| Communication     
	v    
	RDMA NIC     
	|     
	| Network     
	v    
	Remote Node

The CPU/application may simultaneously handle communication controland completion processing:

	CPU Core       
	|       
	+-- Setup QP / MR       
	+-- Post Work Requests       
	+-- Poll CQ       
	+-- Process Completions

If communication becomes slow, the GPU may have to wait beforecontinuing dependent work.

Example:
    
	GPU Compute        
	|        
	v    
	Communication        
	|        
	v    
	Network / RDMA delay        
	|        
	v    
	GPU waits        
	|        
	v    
	Training iteration takes longer

Possible bottlenecks can therefore include:
- GPU compute
- CPU processing
- Completion processing
- Memory bandwidth
- PCIe
- Network bandwidth
- Network latency
- Network congestion
- Packet loss
- Communication synchronization

A low GPU utilization value does not automatically prove that the GPU itself is the problem.

A performance engineer should investigate:

	What is the GPU waiting for?
---
## 12. Key Lessons

1. RDMA WRITE moves payload directly into a permitted remote MR.
2. Ordinary RDMA WRITE does not itself provide a receive completion   
   to notify the remote application.
3. RDMA WRITE WITH IMMEDIATE can combine remote memory data movement   
   with a small immediate value reported in a receive-side completion.
4. The actual payload is stored in memory, not in the CQ.
5. MR, RQ, and CQ have different responsibilities.
6. RQ contains posted Receive Work Requests.
7. CQ contains Work Completions.
8. Applications can poll the CQ to detect completed work.
9. Busy polling can reduce completion-detection latency at the cost   of CPU utilization.
10. Event-driven completion can improve CPU efficiency but may add    event/wake-up overhead.
11. High CPU utilization is not automatically a bottleneck.
12. Performance must be analyzed across GPU, CPU, memory, PCIe,    network, and communication behavior.
---

## Mental Model
    
	MR = Where the data is
    
	RQ = Receive work prepared by the application
    
	CQ = What happened / completion information
    
	Polling = Application checks CQ for completed work
    
	Busy Polling = Lower latency potential, higher CPU usage
   
	Performance Engineering = Find what the workload is waiting for
