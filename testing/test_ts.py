# test_ts.py
import socket
import sys

def test_ts_queries(ts_hostname, ts_port):
    # Define a list of test queries.
    # These queries follow the format: "0 DomainName identification flag"
    # Adjust the queries based on the contents of the TS database being tested.
    test_queries = [
        "0 princeton.com 1 it",       # Expected to match (for TS1, if princeton.com is in the DB)
        "0 www.google.com 2 it",       # Expected to match (for TS1)
        "0 nonexistentsite.com 3 it"   # Expected to not match; should return an nx response.
    ]
    
    for query in test_queries:
        print(f"Sending query: {query}")
        try:
            # Create a TCP connection to the TS server.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ts_hostname, ts_port))
            sock.sendall(query.encode())
            
            # Wait for the response (assuming the response fits in 1024 bytes).
            response = sock.recv(1024).decode().strip()
            print(f"Received response: {response}\n")
            
            sock.close()
        except Exception as e:
            print(f"Error sending query '{query}': {e}\n")

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 test_ts.py <ts_hostname> <ts_port>")
        sys.exit(1)
    
    ts_hostname = sys.argv[1]
    try:
        ts_port = int(sys.argv[2])
    except ValueError:
        print("Error: Port must be an integer.")
        sys.exit(1)
    
    test_ts_queries(ts_hostname, ts_port)

if __name__ == '__main__':
    main()
