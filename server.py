import socket
import time
import random
import json

HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Port to listen on

# Create a socket and bind to the host/port
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()  # Start listening for connections
    print(f"Server listening on {HOST}:{PORT}")

    conn, addr = server_socket.accept()  # Accept a connection
    with conn:
        print(f"Connected by {addr}")
        while True:
            # Generate random live data
            data = [{"x": random.uniform(0, 5), "y": random.uniform(-20, 80)} for _ in range(10)]
            conn.sendall(json.dumps(data).encode('utf-8'))  # Send data as JSON
            time.sleep(1)  # Wait before sending the next batch
