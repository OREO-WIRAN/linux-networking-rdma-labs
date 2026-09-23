# Lab 01 : Linux Network Basics

## Objective

Build a basic Linux networking lab using 
Ubuntu on WSL2 and practice
neteork inspection, connectivity testing,
routing, DNS, and toubleshooting.

## Environment

- Window 11 Pro
- WSL2
- Ubuntu Linux
- Network Interface: ethO

## Commands Used

'''bash
ip addr
ip route
ip neigh
ping -c 4 8.8.8.8
ping -c 4 google.com
ss -tuln
cat /etc/resolv.conf

Network Configuration
During this lab, the Linux environment was configured with:

-IPv4 Address: 172.24.160.77/20
-Network Interface: ethO
-Default Gateway: 172.24.160.1
-Subnet Mask: 255.255.240.0
-Network Address: 172.24.160.0
-Broadcast Address: 172.24.175.255
-MTU: 1500

Connectivity Testing
Two connectivity tests were performed

Test by IP Address

	ping -c 4 8.8.8.8

Result:

-4 packets transmitted
-4 packets received
-0% packet loss

This confirmed that IP connectivity was working.

Test by Domain Name

	ping -c 4 google.com

The test completed successfully with 0% packet loss.

This confirmed that both network connectivity and DNS
name resolution were working.

Routing
The routing table showed:

	default via 172.24.160.1 dev ethO

This means traffic for destinations without a more specific route 
is forworded through the default gateway using the ethO interface.

Troubleshooting Incident
While updating Ubuntu packages, the following error occurred:

	Temporary failure resolving 
	'archive.ubuntu.com'

To determine whether the issue was DNS-only or a wider connectivity problem, I tested direct IP connectivity
and DNS resolution separately.

Both the direct IP ping and domain-name ping intially failed.


I restarting the WSL environment from Windows PowerShell:

	wsl --shutdown

After restarting WSL,I tested the network again.

Both IP connectivity and DNS resolution recovered successfully.

What I Learned
-How to inspect Linux network interfaces and IP address.
-How to read a Linux routing table.
-How to identify a default gateway.
-How to test IP connectivity separately from DNS resolution.
-How to inspect listening TCP and UDP ports.
-How CIDR prefix/20 maps to subnet mask 255.255.240.0
-How to calculate network and broadcast addresses.
-How to troubleshoot a WSL networking failure systematically.

Next Lab
Lab 02 will explore TCP/UDP,ports,sockets,and network services.

 
