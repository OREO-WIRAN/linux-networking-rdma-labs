# Labs 03 - IP Subnet and Routing 
## Objective

Understand IPv4 addressing, subnetting, routing decision, default gateways, 
and neighbor dicovery in linux.

## Environment

- Ubuntu Linux on WSL2
- Interface: ethO
- IPv4 address: 172.24.160.77/20
- Default gateway: 172.24.160.1

## Network Analysis

The host IPv4 address is:
172.24.160.77/20
The /20 prefix means the subnet mask is:
255.255.240.0
Therefore, the local network is:
172.24.160.0/20

## Routing

The Linux routing table showed:

- Local subnet traffic uses ethO directly.
- Traffic outside the local subnet uses the default gateway 172.24.160.1

For example:

8.8.8.8.-> 172.24.160.1 -> ethO
A destination inside the local subnet:
172.24.160.100 -> ethO direactly
No gateway is required for the local destination.

## Neighbor Discovery

The gateway 172.24.160.1 was successsfully reached.
After communication, the neighbor table showed the gateway as REACHABLE
and associated it with a link-layer (MAC) address.

A test to 172.24.160.100 returned Destination Host UNreachable.

The routing decision was still correct because 172.24.160.100 belong to the same subnet, 
but neighbor resolution failed because no reachable host responded for that address.

## What I Learned

- An IP address identifies a layer 3 endpoint.
- A subnet prefix determines which addresses are considered local.
- Linux check its routing table before sending traffic.
- Same-subnet traffic is sent directly through the network interface.
- Remote-subnet traffic is normally sent through a gateway.
- Neighbor discovery maps an IPv4 neighbor to its link-layer address.
- A valid route does not guarantee that the destination host is reachable.

## Result

Successfully inspected IPv4 addressing, calculated the local subnet,
analyzed Linux routing decision, tested local and gateway reachability,
and observed neighbor states including REACHABLE and FAILED.

