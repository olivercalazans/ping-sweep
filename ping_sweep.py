import subprocess
import sys
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed



MAX_THREADS = 100



def get_local_ip():
    """Return the IPv4 address of the interface connected to the network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        
        local_ip = s.getsockname()[0]
        s.close()
        
        return local_ip
    except Exception:
        print("Unable to determine local IP.")
        sys.exit(1)



def generate_ips(base_ip):
    """Generate all IPs in the /24 subnet based on the base IP."""
    parts = base_ip.split('.')
    
    if len(parts) != 4:
        raise ValueError("Invalid IP")
    
    network_prefix = '.'.join(parts[:3])
    return [f"{network_prefix}.{i}" for i in range(1, 255)]  # exclude .0 and .255



def ping_ip(ip):
    """Send 3 pings to the IP and return True if it responds. Command depends on OS"""
    if sys.platform.startswith('win'):
        cmd = ['ping', '-n', '3', '-w', '1000', ip]  # 1s timeout per packet
    else:
        cmd = ['ping', '-c', '3', '-W', '1', ip]     # 1s timeout per packet

    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False



def main():
    local_ip = get_local_ip()
    print(f"Detected local IP: {local_ip}")

    ips = generate_ips(local_ip)
    print(f"Scanning {len(ips)} IPs in /24 subnet with at most {MAX_THREADS} threads...\n")

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
    main()