#!/usr/bin/env python3
import socket
import sys

def load_rs_database(filename):
    
    ts_mapping = {}  
    rs_db = {}   
    try:
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        if len(lines) < 2:
            raise ValueError("RS database must have at least 2 lines for TLD mappings.")
        # Process first two lines as TLD mappings.
        ts1_line = lines[0].split()
        ts2_line = lines[1].split()
        if len(ts1_line) != 2 or len(ts2_line) != 2:
            raise ValueError("TLD mapping lines must have exactly 2 tokens.")
        ts_mapping[ts1_line[0].lower()] = ts1_line[1]
        ts_mapping[ts2_line[0].lower()] = ts2_line[1]
        # Process remaining lines for RS direct mappings.
        for line in lines[2:]:
            parts = line.split()
            if len(parts) == 2:
                domain, ip = parts
                rs_db[domain.lower()] = ip
    except Exception as e:
        print(f"[DEBUG] RS: Error loading database: {e}")
    print(f"[DEBUG] RS TLD mappings: {ts_mapping}")
    print(f"[DEBUG] RS direct mappings: {rs_db}")
    return ts_mapping, rs_db

def is_under_tld(domain, tld):
    domain = domain.lower()
    tld = tld.lower()
    return domain == tld or domain.endswith("." + tld)

def process_query(query, ts_mapping, rs_db, rudns_port, rs_response_file):
    # print(f"[DEBUG] RS processing query: {query}")
    tokens = query.split()
    if len(tokens) != 4 or tokens[0] != "0":
        print("[DEBUG] RS: Invalid query format")
        return None
    _, domain, ident, flag = tokens
    domain_lower = domain.lower()
    response = None
    # Check if domain is under a managed TLD.
    for tld in ts_mapping:
        if is_under_tld(domain_lower, tld):
            ts_hostname = ts_mapping[tld]
            # print(f"[DEBUG] RS: Domain '{domain}' is under TLD '{tld}'; TS hostname: {ts_hostname}")
            if flag == "it":
                response = f"1 {domain} {ts_hostname} {ident} ns"
                # print(f"[DEBUG] RS iterative response: {response}")
                break
            elif flag == "rd":
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ts_sock:
                        # print(f"[DEBUG] RS: Connecting to TS at {ts_hostname}:{rudns_port} for recursive query")
                        ts_sock.connect((ts_hostname, rudns_port))
                        ts_sock.sendall(query.encode())
                        ts_response = ts_sock.recv(1024).decode().strip()
                        # print(f"[DEBUG] RS: Received recursive response from TS: {ts_response}")
                    ts_tokens = ts_response.split()
                    if len(ts_tokens) == 5:
                        if ts_tokens[4] == "aa":
                            ts_tokens[4] = "ra"
                        response = " ".join(ts_tokens)
                    else:
                        response = f"1 {domain} 0.0.0.0 {ident} nx"
                except Exception as e:
                    print(f"[DEBUG] RS: Exception contacting TS: {e}")
                    response = f"1 {domain} 0.0.0.0 {ident} nx"
                break
    if response is None:
        # Domain is not under any managed TLD; use RS direct mappings.
        if domain_lower in rs_db:
            ip = rs_db[domain_lower]
            response = f"1 {domain} {ip} {ident} aa"
            # print(f"[DEBUG] RS: Found direct mapping for '{domain}': {response}")
        else:
            response = f"1 {domain} 0.0.0.0 {ident} nx"
            print(f"[DEBUG] RS: No direct mapping for '{domain}', response: {response}")
    # Log response to file.
    try:
        with open(rs_response_file, "a") as f:
            f.write(response + "\n")
    except Exception as e:
        print(f"[DEBUG] RS: Error writing to {rs_response_file}: {e}")
    return response

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 rs.py <rudns_port>")
        sys.exit(1)
    try:
        rudns_port = int(sys.argv[1])
    except ValueError:
        print("[DEBUG] RS: Port must be an integer.")
        sys.exit(1)
    rs_response_file = "rsresponses.txt"
    ts_mapping, rs_db = load_rs_database("rsdatabase.txt")
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_sock.bind(("", rudns_port))
    except Exception as e:
        print(f"[DEBUG] RS: Error binding socket: {e}")
        sys.exit(1)
    server_sock.listen(5)
    print(f"[DEBUG] RS server listening on port {rudns_port}")
    while True:
        conn, addr = server_sock.accept()
        print(f"[DEBUG] RS accepted connection from {addr}")
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    print("[DEBUG] RS: No more data; closing connection")
                    break
                query = data.decode().strip()
                print(f"[DEBUG] RS received query: {query}")
                response = process_query(query, ts_mapping, rs_db, rudns_port, rs_response_file)
                if response:
                    print(f"[DEBUG] RS sending response: {response}")
                    conn.sendall(response.encode())
                else:
                    print("[DEBUG] RS: No response generated for the query")

if __name__ == '__main__':
    main()
