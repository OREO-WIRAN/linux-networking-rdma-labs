# Lab 12: RDMA Environment Discovery and Fundamentals
## Objective
Explore RDMA support in the current Linux/WSL2 environment and understandthe fundamental components and operations used by RDMA.
## Environment
- Linux on WSL2
- Kernel: 6.18.33.2-microsoft-standard-WSL2
- RDMA userspace command available
- No RDMA device exposed to the current WSL2 environment
- Soft-RoCE (rdma_rxe) kernel module not available

## 1. RDMA Environment Discovery
Commands used:
    
	uname -r    
	ls /sys/class/infiniband    
	which rdma    
	rdma link show    
	rdma dev show    
	modinfo rdma_rxe    
	lsmod | grep rdma

### Results
Kernel:
 
   6.18.33.2-microsoft-standard-WSL2

RDMA command:

    /usr/bin/rdma

No `/sys/class/infiniband` directory was available.
`rdma link show` and `rdma dev show` returned no RDMA devices.

Soft-RoCE module check:
    modinfo: ERROR: Module rdma_rxe not found.

### Conclusion
Having RDMA userspace tools does not mean that an RDMA device orRDMA-capable kernel driver is available.
The current WSL2 environment can be used to study RDMA concepts,
but it cannot currently run an RXE/Soft-RoCE RDMA data-path labwithout additional kernel/device support.

## 2. RDMA Architecture
RDMA stands for:
    Remote Direct Memory Access
It allows data transfer involving registered memory across nodeswhile reducing CPU and kernel involvement in the data path.

Basic architecture:
    
	Application         
	|         
	v        
	QP     
	+-------+     
	|  SQ   |  Send Queue     
	|  RQ   |  Receive Queue     
	+-------+         
	|         
	v      
	RDMA NIC         
	|       
	Network         
	|         
	v      
	RDMA NIC         
	|         
	v        
	MR

## 3. Memory Region (MR)
Memory must be registered before it can be used for RDMA operations.
An MR contains information such as:
- Memory address
- Length
- Access permissions
- lkey
- rkey

Conceptually:
    
	Memory       
	|       
	| Register       
	v    
	+----------------+    
	| Memory Region  |    
	| address        |    
	| length         |    
	| permissions    |    
	| lkey / rkey    |    
	+----------------+

`lkey` is used for local memory access by RDMA operations.
`rkey` is used to authorize permitted remote access to a registeredMemory Region.

## 4. Queue Pair (QP)
A Queue Pair contains:
    
	SQ = Send Queue    
	RQ = Receive Queue

Applications post Work Requests to queues to request RDMA operations.

## 5. Completion Queue (CQ)
The Completion Queue contains Work Completions generated forcompleted RDMA work.
A completion does not mean that the remote application has alreadyprocessed the data.
For example:

	RDMA WRITE completed             
		!=    
	Remote application processed the data

## 6. SEND vs RDMA WRITE vs RDMA READ

### SEND / RECEIVE

	Node A -----------------> Node B             
		SEND

Node B must prepare a Receive Work Request.

### RDMA WRITE

	Node A -----------------> Node B MR           
		RDMA WRITE

Node A writes data to permitted registered memory on Node B.
The remote side does not need to post a Receive Work Request forthe RDMA WRITE data transfer itself.

### RDMA READ

	Node A <----------------- Node B MR           
		RDMA READ data
Node A initiates the operation, but the data moves from theremote memory on Node B back to Node A.

## 7. Example

Node B:

	Remote Address = 0x1000    
	rkey           = 789    
	Permission     = Remote Write

Node A wants to write:

	"HELLO"

Conceptually:

	Node A                         Node B

	Local MR                       Remote MR    
	["HELLO"]                      [ empty ]        
	    |                              ^        
	    |        RDMA WRITE            |        
	    +------------------------------+                                       
					   |                                       
					   v                                   
					["HELLO"]

The remote address, rkey, permissions, and memory range must bevalid for the operation.

## What I Learned
- RDMA means Remote Direct Memory Access.
- RDMA reduces CPU and kernel involvement in the data path.
- Memory must be registered for RDMA operations.
- MR represents registered memory.
- QP contains Send and Receive Queues.
- CQ reports Work Completions.
- lkey is associated with local memory access.
- rkey is used to authorize permitted remote memory access.
- SEND/RECEIVE requires the receiver to prepare a Receive Work Request.
- RDMA WRITE can write directly to permitted remote registered memory.
- RDMA READ reads data from permitted remote registered memory.
- Data transfer completion does not mean the remote application 
  has  already processed the data.
- Userspace RDMA tools alone do not guarantee RDMA hardware or kernel support.
