# test_rs.py
import socket
import sys

def test_rs_queries(rs_hostname, rs_port):
    # List of test queries (in RU-DNS format: "0 DomainName identification flag")
    test_queries = [
        # Iterative query: domain falls under a managed TLD.
        # For example, if "princeton.com" is under the managed TLD "com",
        # RS should respond with an NS response (redirecting to the TS server).
        "0 princeton.com 1 it",
        # Recursive query: RS should forward to TS and, if TS returns an authoritative answer,
        # change the flag to "ra" before returning.
        "0 princeton.com 2 rd",
        # Direct RS mapping: if the RS database has a direct mapping (e.g., "github.io"),
        # RS should return an authoritative answer (aa).
        "0 github.io 3 it",
        # Non-existent domain: RS should return NX (with IP 0.0.0.0).
        "0 nonexistentsite.com 4 it"
    ]
    
    for query in test_queries:
        print(f"Sending query: {query}")
        try:
            # Connect to the RS server.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((rs_hostname, rs_port))
            sock.sendall(query.encode())
            
            # Receive and print the response (assuming it fits within 1024 bytes).
            response = sock.recv(1024).decode().strip()
            print(f"Received response: {response}\n")
            sock.close()
        except Exception as e:
            print(f"Error sending query '{query}': {e}\n")

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 test_rs.py <rs_hostname> <rs_port>")
        sys.exit(1)
    rs_hostname = sys.argv[1]
    try:
        rs_port = int(sys.argv[2])
    except ValueError:
        print("Error: Port must be an integer.")
        sys.exit(1)
    
    test_rs_queries(rs_hostname, rs_port)

if __name__ == '__main__':
    main()
