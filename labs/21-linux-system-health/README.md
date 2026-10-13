# Lab 21 - Linux System Health & Troubleshooting

## Objective

Practice a structured Linux troubleshooting workflow by collecting and correlating evidence across:

- CPU and system load
- Process states and process relationships
- Memory and swap
- Disk capacity and I/O
- Network connectivity and DNS
- System logs and incident timing

The goal is not to diagnose a bottleneck from a single metric, 
but to use multiple Linux observability tools to correlate system-, device-, 
and process-level evidence before forming a bottleneck hypothesis.

## Environment

- Ubuntu 26.04.1 LTS on WSL2
- Linux kernel: 6.18.33.2-microsoft-standard-WSL2
- Architecture: x86-64
- 8 logical processing units reported by `nproc`
- Virtualized storage and networking through WSL2
---
##  Baseline System Health

Initial check included:
'''bash
uptime
nproc
free -h
df -h
top
'''
Observed during the lab:

- `nproc` reported 8 logical processing units.
- Load average was low during the baseline observation.
- Approximately 7.2 GiB of memory was available.
- 2.0 GiB of swap was configured and no swap was in use.
- The WSL root filesystem had substantial free capacity.
- CPU was essentially idle during the `top` snapshot.
- No zombie processes were observed in the inspected snapshot.

These observations did not show CPU, memory, or disk-capacity pressure at the time of measurement.

A single healthy-looking snapshot does not prove that the system has no performance problems. 
Measurements must be correlated with the time when the reported symptom occurs.

---

## Process States and Zombie Investigation

Process inspection included:

```bash
ps aux
ps aux --sort=-%cpu | head
ps aux --sort=-%mem | head
ps -eo pid,ppid,stat,comm | head
pstree -p | head -30
ps aux | awk '$8 ~ /^Z/'
```

Important process states:

- `R` - running or runnable
- `S` - interruptible sleep
- `D` - uninterruptible sleep, often associated with I/O or kernel waits
- `Z` - zombie process

A zombie process has already exited, but its direct parent has not yet collected the child's exit status.

When investigating a zombie, the first step is to identify its direct parent using the zombie's PPID. 
Sending `kill -9` to the zombie itself does not solve the underlying reaping problem.

No zombie processes were observed during the lab snapshot.

---

## CPU and Load Interpretation

Linux load average should not be interpreted as CPU utilization alone.

Load can include:

- Runnable tasks waiting for CPU time
- Tasks in uninterruptible sleep, often associated with I/O waits

Useful evidence to correlate includes:

```bash
uptime
nproc
top
vmstat 1 5
ps aux --sort=-%cpu | head
```

For CPU pressure, a useful pattern is:

- `r` consistently high relative to the number of logical processing units
- Very low CPU idle (`id`)
- Multiple processes in `R` state
- Low `b` and low I/O wait (`wa`) when I/O is not the main source of pressure

A load average greater than the number of logical CPUs does not by itself prove a CPU bottleneck. 
Process states and CPU activity must be correlated before forming a diagnosis.
---

## Memory Pressure Interpretation

Memory investigation included:

```bash
free -h
vmstat 1 5
ps aux --sort=-%mem | head
```

Important evidence includes:

- `available` memory, rather than only the `free` column
- Swap usage
- Active swap-in (`si`) and swap-out (`so`)
- Memory usage of individual processes

During the baseline observation, approximately 7.2 GiB of memory was available and swap usage was zero. No memory pressure was visible in that snapshot.

Swap usage alone does not prove active memory pressure. Low available memory together with sustained `si` and `so` activity provides stronger evidence that 
the system is actively moving memory between RAM and swap.
---

## I/O Pressure Correlation

I/O investigation used multiple levels of evidence:

```bash
vmstat 1 5
iostat -xz 1 5
sudo iotop
ps -eo pid,ppid,stat,%cpu,%mem,cmd
```

The tools provide different perspectives:

- `vmstat` provides system-level evidence such as runnable tasks (`r`), blocked tasks (`b`), and I/O wait (`wa`).
- `iostat` provides device-level evidence including operations per second, throughput, completion latency (`await`), and device utilization (`%util`).
- `iotop` helps identify processes generating disk reads or writes.
- `ps` provides process state, PID/PPID relationships, CPU usage, memory usage, and command context.

During the baseline `vmstat` observation:

- `b` was 0.
- I/O wait was approximately 0%.
- Swap-in and swap-out were 0.

During the baseline `iostat` observation, device utilization and I/O latency were low, with no sustained I/O pressure visible in the sampled intervals.

A stronger I/O-pressure hypothesis would require correlated evidence such as:

- Increasing or sustained blocked tasks (`b`)
- High I/O wait (`wa`)
- Processes in `D` state
- Elevated device latency such as `r_await` or `w_await`
- High device activity or utilization
- A process generating significant I/O in `iotop`

High `%util` alone does not prove that a disk is failing. Device metrics must be interpreted together with latency, queueing, workload, process state, and application context.
---

## Controlled I/O Experiment

A controlled write workload was created to observe process-level I/O behavior.

First, a 256 MiB file was written using `dd`:

```bash
dd if=/dev/zero of=~/io-test.bin bs=1M count=256
```

The command completed in approximately 0.20 seconds.

A direct-I/O test was then performed:

```bash
dd if=/dev/zero of=~/io-test-slow.bin bs=1M count=256 oflag=direct status=progress
```

Observed result:

```text
256 MiB copied in approximately 0.208 seconds
reported throughput: approximately 1.3 GB/s
```

Because the `dd` process existed for only about 0.208 seconds, it could complete between `iotop` refresh intervals. 
Not observing a short-lived process in a monitoring snapshot does not prove that the I/O did not occur.

The reported 1.3 GB/s should not be interpreted as a benchmark of the physical SSD. The experiment ran inside WSL2 with a virtualized storage stack.

To create a longer observation window without generating a very large file, a Python workload wrote 4 MiB blocks repeatedly, 
called `fsync()` after each write, and paused between iterations.

The workload performed:

```text
4 MiB x 20 iterations = 80 MiB
```

The terminal reported progress from 4 MiB through 80 MiB, and the resulting file size was verified with:

```bash
ls -lh ~/io-live-test.bin
```

Observed file size:

```text
80M
```

This confirmed that the controlled write workload occurred even when an `iotop` snapshot did not capture active write throughput.
---

## iotop Limitation in WSL2

`iotop` was installed and used to inspect process-level disk I/O.

The WSL2 environment displayed the warning:

```text
CONFIG_TASK_DELAY_ACCT and kernel.task_delayacct sysctl not enabled in kernel,
cannot determine SWAPIN and IO %
```

Therefore, some `iotop` metrics such as `SWAPIN` and `IO%` were not available in this environment.

Process-level disk read/write information could still be useful, but missing metrics must not be interpreted as evidence that no I/O activity occurred.

This demonstrates an important troubleshooting principle:

> Observability depends on the capabilities of the operating environment and kernel. Missing telemetry is not the same as zero activity.
---
## Network Connectivity and DNS Investigation
Network investigation included:
```bash
ip -br link
ip -br addr
ip route
ping -c 4 172.24.160.1
ping -c 4 1.1.1.1
ping -c 4 google.com
getent hosts google.com
cat /etc/resolv.conf```

Observed during the lab:
- `eth0` was UP.- The system had an IPv4 address and a default route.
- The default gateway was reachable with no packet loss in the sample.
- `1.1.1.1` was reachable, although latency varied during the sample.
- `google.com` resolved successfully and was reachable.
- `/etc/resolv.conf` used `10.255.255.254` as the nameserver.
- `getent hosts google.com` successfully returned addresses.
These observations showed that network connectivity and DNS resolution were functioning during the current checks.
Successful IP connectivity combined with failed hostname resolution would make DNS a strong investigation target, 
but the failure should still be verified with additional evidence.
---

## System Logs and Incident Timing

System logs were inspected using:

```bash
journalctl -p err -b
journalctl -p err -b -n 10
journalctl --since "YYYY-MM-DD HH:MM" --until "YYYY-MM-DD HH:MM"
```

Historical WSL-related errors included `getaddrinfo()` failures, indicating that name-resolution failures had occurred previously.

However, current DNS tests succeeded during the lab.

This demonstrates that log entries must be correlated with incident timing.

An old error does not prove that the same failure is occurring now. Useful troubleshooting questions include:

- When did the user-visible problem occur?
- Does the log timestamp overlap with the incident?
- Can the failure be reproduced now?
- Do current system and network measurements support the same hypothesis?

Historical logs provide context, while time-correlated evidence provides stronger support for root-cause analysis.
---

## Structured Troubleshooting Workflow

The lab reinforced the following troubleshooting workflow:

1. Establish a baseline before changing the system.
2. Identify the time window in which the problem occurred.
3. Collect evidence from multiple levels:
   - system
   - process
   - memory
   - storage
   - network
   - logs
4. Correlate metrics instead of relying on a single value.
5. Form a bottleneck hypothesis from the evidence.
6. Identify the process, device, or subsystem associated with the symptoms.
7. Investigate workload and application context before taking corrective action.
8. Apply the least disruptive appropriate action.
9. Measure again to verify whether the problem improved.

A suspect is not automatically the root cause.

For example, a process generating high disk I/O should be investigated in context before it is terminated. 
The workload may be expected and another component may be responsible for the observed performance problem.
---

## Key Takeaways

- Linux load average is not the same as CPU utilization.
- High load must be correlated with runnable tasks, blocked tasks, CPU activity, I/O wait, and process states.
- Low `free` memory alone does not prove memory pressure; `available` memory, swap activity, and process usage provide better context.
- A zombie process should be investigated through its direct parent rather than killed directly.
- Disk `%util` alone does not prove a storage failure or bottleneck.
- `vmstat`, `iostat`, `iotop`, and `ps` provide complementary system-, device-, and process-level evidence.
- A monitoring snapshot can miss short-lived processes.
- Missing telemetry does not mean zero activity.
- Successful IP connectivity with failed hostname resolution makes DNS a strong investigation target.
- Historical log errors must be correlated with the incident time.
- A high-resource process is a suspect to investigate, not automatically the root cause.
- Troubleshooting should follow an evidence-driven cycle: measure, correlate, hypothesize, investigate, remediate, and verify.

## Conclusion

This lab practiced evidence-driven Linux troubleshooting across CPU, memory, processes, storage I/O, networking, DNS, and system logs.

The main lesson is that no single metric should be used in isolation to declare a bottleneck. 
Reliable diagnosis requires correlating evidence across multiple layers and validating the hypothesis against workload and incident context before taking corrective action.
