# Lab 02 - TCP, UDP and Ports

## Objective

Understand TCP/UDP sockers,listening ports,and client-server communication in Linux.

## Environment

- Ubuntu Linux on WSL2
- Python 3
- Linux 'ss' command
- curl

## Lab

Started a simple HTTP server:
	python3 -m http.server 8080

Vertified that TCP port 8080 was listening:
	ss -tln | grep 8080

Tested the server from a client:
	curl http://127.0.0.1:8080

The server returned an HTTP reponse successsfully.

## What I Learned

- An IP address identifies a host/network interface.
- A port identifies a network service or application endpoint.
- TCP provides connection-oriented and reliable data delivery.
- A server uses a listening socket to wait for client connections.
- 'ss' can be used to inspect Linux network sockers.
- 'curl' can act as a client to test an HTTP service.

## Result

TCP part 8080 successfully entered the LISTEN state and the HTTP client successfully communicated with the Python server.


