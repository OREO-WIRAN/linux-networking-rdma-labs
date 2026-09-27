# Lab 06 - ARP and Neighbor Discovery
## Objective

Understand how Linux resolves an IPv4 address to a MAC address using ARP
and how the Linux neighbor table changes when network traffic is generated.

This is an important networking foundation for Ethernet-based RDMA and RoCE.

## Environment
- Linux
- Interface: eth0
- Gateway: 172.24.160.1
- Tools: ip, ping

## Step 1 - Inspect the Neighbor Table
Command:
	ip neigh
Example result: 
	172.24.160.1 dev eth0 lladdr
00:15:5d:05:2e:2c STALE

The neighbor table maps an IPv4 address to a Layer 2 MAC address.
The STALE state means that Linux has cached neighbor entry, but its reacability 
has not been recentry confirmed.

## Step2 - Generate Traffic
Command:
	ping -c 1 172.24.160.1
Result:
	1 packets transmitted, 1 received,0% packet loss
After generatig traffic, check the neighbor table again:
	ip neigh
The neighbor state changed to:
	REACHABLE
This means Linux recentry confirmed that the neighbor is reachable.

## Step3 - Delete the Neighbor Entry
Command:
	sudo ip neigh del 172.24.160.1 dev eth0
Then verify:
	ip neigh
The entry was removed from the neighbor table.

##Step4 - Trigger ARP Resolution Again
Generate traffic again:
	ping -c 1 172.24.160.1
Then inspect the neighbor table:
	ip neigh
Result:
	172.24.160.1. dev eth0 lladdr
00:15:5d:05:2e:2c REACHABLE

Linux recreated the neighbor entry after network traffic was generated.

## What I Learned
This lab demonstrates the relationship between:

-IPv4 addresses
-MAC addresses
-ARP
-Linux neighbor cache
-STALE and REACHABLE neighbor states

When an IPv4 host needs to communicate with another host on the local
Ethernet network, it needs the destination MAC address. ARP provides the
mapping between the IPv4 address and the Layer 2 MAC address.

Linux stores this information in the neighbor table.

## Relevance to RDMA and RoCE

RoCE (RDMA over Converged Ethernet) operates over Ethernet networks.
Understanding Layer 2 addressing and neighbor resolution is therefore 
an important foundation for troubleshooting RoCE connectivity.

Problems involving neighbor resolution, VLAN configuration, routing, MTU,
or Layer 2 connectivity can prevent hosts from communicating correctly
before RDMA communication is even established.

This lab builds the networking foundation required for later RDMA and NVIDIA ConnectX labs. 
