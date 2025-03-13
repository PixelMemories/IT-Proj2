#!/usr/bin/env python3
import socket
import sys

def load_ts_database(filename):
    
    ts_db = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) == 2:
                        domain, ip = parts
                        ts_db[domain.lower()] = (domain, ip)
    except Exception as e:
        print(f"[DEBUG] TS1: Error loading database: {e}")
    print(f"[DEBUG] TS1 loaded database: {ts_db}")
    return ts_db

def process_query(query, ts_db, ts_response_file):
    # print(f"[DEBUG] TS1 processing query: {query}")
    tokens = query.split()
    if len(tokens) != 4 or tokens[0] != "0":
        print("[DEBUG] TS1: Invalid query format")
        return None
    _, domain, ident, flag = tokens
    domain_lower = domain.lower()
    if domain_lower in ts_db:
        stored_domain, ip = ts_db[domain_lower]
        response = f"1 {stored_domain} {ip} {ident} aa"
        print(f"[DEBUG] TS1: Found mapping for {domain}, response: {response}")
    else:
        response = f"1 {domain} 0.0.0.0 {ident} nx"
        print(f"[DEBUG] TS1: No mapping found for {domain}, response: {response}")
    # Log response to file.
    try:
        with open(ts_response_file, "a") as f:
            f.write(response + "\n")
    except Exception as e:
        print(f"[DEBUG] TS1: Error writing to {ts_response_file}: {e}")
    return response

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 ts1.py <rudns_port>")
        sys.exit(1)
    try:
        rudns_port = int(sys.argv[1])
    except ValueError:
        print("[DEBUG] TS1: Port must be an integer.")
        sys.exit(1)
    ts_response_file = "ts1responses.txt"
    ts_db = load_ts_database("ts1database.txt")
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_sock.bind(("", rudns_port))
    except Exception as e:
        print(f"[DEBUG] TS1: Error binding socket: {e}")
        sys.exit(1)
    server_sock.listen(5)
    print(f"[DEBUG] TS1 server listening on port {rudns_port}")
    while True:
        conn, addr = server_sock.accept()
        print(f"[DEBUG] TS1 accepted connection from {addr}")
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    print("[DEBUG] TS1: No more data; closing connection")
                    break
                query = data.decode().strip()
                print(f"[DEBUG] TS1 received query: {query}")
                response = process_query(query, ts_db, ts_response_file)
                if response:
                    print(f"[DEBUG] TS1 sending response: {response}")
                    conn.sendall(response.encode())
                else:
                    print("[DEBUG] TS1: No response generated")

if __name__ == '__main__':
    main()
