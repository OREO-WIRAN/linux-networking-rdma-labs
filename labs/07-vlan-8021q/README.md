# Lab 07 — 802.1Q VLAN Configuration and Troubleshooting

## Objective

This lab demonstrates how to configure IEEE 802.1Q VLAN interfaces
using Linux network namespaces and troubleshoot connectivity caused
by a VLAN mismatch.

## Lab Topology

hostA
- Interface: ethA.100
- VLAN ID: 100
- IPv4: 10.100.0.1/24

hostB
- Interface: ethB.100
- VLAN ID: 100
- IPv4: 10.100.0.2/24

The two hosts are connected using a Linux veth pair.

## VLAN Configuration

802.1Q VLAN interfaces were created on both hosts.

Example verification:

    ip -d link show ethA.100
    ip -d link show ethB.100

Both interfaces showed:

    vlan protocol 802.1Q id 100

## Connectivity Test

With both hosts configured for VLAN 100, connectivity succeeded.

    hostA -> 10.100.0.2
    hostB -> 10.100.0.1

Result:

    3 packets transmitted, 3 received, 0% packet loss

## VLAN Mismatch Troubleshooting

To simulate a network configuration failure, hostB was changed
from VLAN 100 to VLAN 200 while hostA remained on VLAN 100.

The ping test failed:

    3 packets transmitted, 0 received, 100% packet loss

The neighbor table on hostA showed:

    10.100.0.2 dev ethA.100 FAILED

This demonstrated that hosts using different VLAN IDs cannot
communicate at Layer 2 even when their IPv4 addresses are in the
same subnet.

## Recovery

hostB was changed back from VLAN 200 to VLAN 100.

The neighbor cache on hostA was flushed and connectivity was
tested again.

Result:

    3 packets transmitted, 3 received, 0% packet loss

The neighbor entry changed from FAILED to REACHABLE and later
STALE, confirming successful Layer 2 neighbor resolution.

## Key Takeaways

- IEEE 802.1Q provides VLAN tagging on Ethernet networks.
- Hosts must use matching VLAN IDs for direct Layer 2 communication.
- Matching IP subnets alone do not guarantee connectivity.
- A VLAN mismatch can cause ARP/neighbor resolution to fail.
- Linux `ip link`, `ip addr`, `ip neigh`, and `ping` are useful
  tools for diagnosing VLAN connectivity problems.
- REACHABLE and STALE are valid Linux neighbor states.
- FAILED indicates unsuccessful neighbor resolution.

## Relevance to RDMA and RoCE

RoCE operates over Ethernet networks, so correct Layer 2
configuration is essential before RDMA communication can work.

VLAN mismatches, Layer 2 connectivity problems, MTU mismatches,
and neighbor-resolution failures can prevent RoCE endpoints from
communicating.

Understanding 802.1Q VLAN configuration and troubleshooting is
therefore an important networking foundation for RDMA and
NVIDIA AI infrastructure.
