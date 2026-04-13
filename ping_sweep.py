import subprocess
import sys
import socket
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


MAX_THREADS = 100



def abort(msg: str):
    print(msg)
    sys.exit(1)



def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))

        local_ip = s.getsockname()[0]
        s.close()

        return local_ip

    except Exception:
        abort("Unable to determine local IP.")



def mask_to_cidr(mask: str) -> int:
    try:
        parts = mask.split('.')

        if len(parts) != 4:
            raise ValueError

        binary = ''.join(f"{int(p):08b}" for p in parts)
        return binary.count('1')

    except Exception:
        abort('Unable to define the network mask')



def get_network_cidr(local_ip: str) -> int:
    try:
        if sys.platform.startswith('win'):
            return get_net_cidr_on_windows(local_ip)
        else:
            return get_net_cidr_on_linux(local_ip)
    except Exception:
        abort("Unable to get network mask")



def get_net_cidr_on_windows(local_ip: str):
    output = subprocess.check_output(['netsh', 'interface', 'ip', 'show', 'addresses'], text=True, encoding='utf-8', errors='replace')        
    lines  = output.splitlines()
    
    for i, line in enumerate(lines):
        if local_ip not in line:
            continue
        
        for j in range(i, min(i + 5, len(lines))):
            match = re.search(r'/(\d+)', lines[j])
            
            if match:
                return int(match.group(1))

    return None    



def get_net_cidr_on_linux(local_ip: str):
    output = subprocess.check_output(['ip', '-4', 'addr', 'show'], text=True, stderr=subprocess.DEVNULL)
    
    for line in output.splitlines():
        if local_ip not in line or 'inet' not in line:
            continue
        
        match = re.search(r'inet \d+\.\d+\.\d+\.\d+/(\d+)', line)
    
        if match:
            return int(match.group(1))

    return None



def generate_ips(base_ip: str, cidr: int) -> list:
    parts = base_ip.split('.')

    if len(parts) != 4:
        abort(f"Invalid IP: {base_ip}")
    
    ip_int    = (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
    mask      = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
    network   = ip_int & mask
    broadcast = network | (~mask & 0xFFFFFFFF)
    first     = network + 1 if network != ip_int else network + 1
    last      = broadcast - 1
    
    if last - first > 65534:
        print(f"Warning: subnet /{cidr} is very large ({last - first + 1} hosts). Scanning may be slow.")
    
    ips = []
    for host in range(first, last + 1):
        ips.append(f"{(host >> 24) & 0xFF}.{(host >> 16) & 0xFF}.{(host >> 8) & 0xFF}.{host & 0xFF}")
    
    return ips



def ping_ip(ip: str):
    if sys.platform.startswith('win'):
        cmd = ['ping', '-n', '3', '-w', '1000', ip]
    else:
        cmd = ['ping', '-c', '3', '-W', '1', ip]

    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False



def main():
    local_ip = get_local_ip()
    print(f"Detected local IP: {local_ip}")
    
    cidr = get_network_cidr(local_ip)
    
    if cidr is None:
        cidr = 24
        print(f"Could not detect subnet mask. Assuming /{cidr} (fallback).")
    else:
        print(f"Detected network CIDR: /{cidr}")
    
    ips = generate_ips(local_ip, cidr)
    print(f"Scanning {len(ips)} IPs (subnet /{cidr}) with at most {MAX_THREADS} threads...\n")
    
    len_active = 0
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_ip = {executor.submit(ping_ip, ip): ip for ip in ips}
    
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                if future.result():
                    print(f"IP RESPONDED: {ip}")
                    len_active += 1
            except Exception as e:
                print(f"Error testing {ip}: {e}")
    
    print(f"\nScan complete. Total active IPs: {len_active}")




if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("Process stopped")
    except Exception as err:  print(f"Unknown error: {err}")
