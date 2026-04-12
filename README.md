# Ping Sweep – Simple Host Discovery

A lightweight, portable ping sweep tool that discovers active hosts on your local network using nothing but the standard `ping` command.  
**No external dependencies** – just pure Python and `ping`. Works on **Linux** and **Windows**.

## Features

- **No extra libraries** – uses only `subprocess`, `socket`, and `concurrent.futures` from the Python standard library.
- **Cross‑platform** – automatically adapts the ping command and timeout flags for Windows (`-n 3 -w 1000`) or Linux/macOS (`-c 3 -W 1`).
- **Automatic CIDR detection** – detects the subnet mask (CIDR) of the active network interface.
- **Adjustable concurrency** – the number of simultaneous pings is controlled by the `MAX_THREADS` variable (default 100). Change it to fit your machine and network.
- **Real‑time output** – prints each IP as soon as it responds.


## How it works

1. Detects your local IP address (the one used to reach the internet).
2. Detects the network CIDR by inspecting the system’s network configuration (`ip addr` on Linux, `ipconfig` on Windows).
3. Generates all IP addresses in that subnet (excluding network and broadcast addresses).
4. Pings each IP with 3 packets and a short timeout (1 second per packet, 5 seconds total).
5. Uses a thread pool with `MAX_THREADS` workers to limit simultaneous pings.
6. Prints each live IP immediately when it replies.

## Usage

```bash
python3 ping_sweep.py
```
