#!/usr/bin/env python3
import socket
import sys

def load_hostnames(filename):
    
    queries = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) == 2:
                        queries.append((parts[0], parts[1]))
                    else:
                        print(f"[DEBUG] Client: Invalid line format: {line}")
    except Exception as e:
        print(f"[DEBUG] Client: Error reading hostnames file: {e}")
    print(f"[DEBUG] Client loaded queries: {queries}")
    return queries

def send_query(hostname, port, message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # print(f"[DEBUG] Client connecting to {hostname}:{port} with message: {message}")
        s.connect((hostname, port))
        s.sendall(message.encode())
        response = s.recv(1024).decode().strip()
        # print(f"[DEBUG] Client received response: {response}")
        s.close()
        return response
    except Exception as e:
        print(f"[DEBUG] Client error connecting to {hostname}:{port} -> {e}")
        return None

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 client.py <rs_hostname> <rudns_port>")
        sys.exit(1)
    rs_hostname = sys.argv[1]
    try:
        rudns_port = int(sys.argv[2])
    except ValueError:
        print("[DEBUG] Client: Port must be an integer.")
        sys.exit(1)
    
    queries = load_hostnames("hostnames.txt")
    if not queries:
        print("[DEBUG] Client: No queries found.")
        sys.exit(1)
    
    try:
        resolved_file = open("resolved.txt", "w")
    except Exception as e:
        print(f"[DEBUG] Client: Error opening resolved.txt: {e}")
        sys.exit(1)
    
    current_id = 1
    for domain, flag in queries:
        query_msg = f"0 {domain} {current_id} {flag}"
        # print(f"[DEBUG] Client sending query to RS: {query_msg}")
        response = send_query(rs_hostname, rudns_port, query_msg)
        if response:
            resolved_file.write(response + "\n")
            parts = response.split()
            if len(parts) == 5:
                resp_flag = parts[4]
                # For iterative queries, if RS returns an NS response, follow the pointer.
                if flag == "it" and resp_flag == "ns":
                    ts_hostname = parts[2]  # TS hostname from RS response.
                    current_id += 1
                    ts_query_msg = f"0 {domain} {current_id} it"
                    print(f"[DEBUG] Client iterative resolution: Sending query to TS at {ts_hostname}:{rudns_port}: {ts_query_msg}")
                    ts_response = send_query(ts_hostname, rudns_port, ts_query_msg)
                    if ts_response:
                        resolved_file.write(ts_response + "\n")
                    else:
                        print("[DEBUG] Client: No response received from TS.")
        else:
            print("[DEBUG] Client: No response received from RS.")
        current_id += 1
    
    resolved_file.close()
    print("[DEBUG] Client: Finished processing queries. Check resolved.txt for results.")

if __name__ == '__main__':
    main()
