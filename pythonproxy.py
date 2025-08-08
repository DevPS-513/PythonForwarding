import socket
import threading
import logging
import signal
import sys

BUFFER_SIZE = 4096  # Size of the buffer for data transfer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def handle_tcp(client_socket, target_ip, target_port):
    try:
        # Connect to the target
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((target_ip, target_port))

        # Forward data between client and target
        def forward_data(source, destination):
            while True:
                data = source.recv(BUFFER_SIZE)
                if not data:
                    break
                destination.sendall(data)

        # Start threads for bidirectional communication
        thread1 = threading.Thread(target=forward_data, args=(client_socket, target_socket), daemon=True)
        thread2 = threading.Thread(target=forward_data, args=(target_socket, client_socket), daemon=True)
        thread1.start()
        thread2.start()

        # Wait for threads to finish
        thread1.join()
        thread2.join()
    except Exception as e:
        logging.error(f"TCP Error: {e}")
    finally:
        client_socket.close()
        target_socket.close()

def handle_udp(local_socket, target_ip, target_port):
    try:
        while True:
            # Receive data from the client
            data, client_address = local_socket.recvfrom(BUFFER_SIZE)
            # Forward data to the target
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            target_socket.sendto(data, (target_ip, target_port))
            # Receive response from the target
            response, _ = target_socket.recvfrom(BUFFER_SIZE)
            # Send the response back to the client
            local_socket.sendto(response, client_address)
            target_socket.close()
    except Exception as e:
        logging.error(f"UDP Error: {e}")
    finally:
        local_socket.close()

def start_proxy(listen_ip, listen_port, target_ip, target_port, protocol):
    try:
        if protocol == "tcp":
            # Start a TCP proxy
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind((listen_ip, listen_port))
            server.listen(5)
            logging.info(f"TCP Proxy listening on {listen_ip}:{listen_port}, forwarding to {target_ip}:{target_port}")

            while True:
                client_socket, addr = server.accept()
                logging.info(f"TCP Connection received from {addr}")
                thread = threading.Thread(target=handle_tcp, args=(client_socket, target_ip, target_port), daemon=True)
                thread.start()

        elif protocol == "udp":
            # Start a UDP proxy
            server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server.bind((listen_ip, listen_port))
            logging.info(f"UDP Proxy listening on {listen_ip}:{listen_port}, forwarding to {target_ip}:{target_port}")

            handle_udp(server, target_ip, target_port)
    except Exception as e:
        logging.error(f"Proxy Error: {e}")
    finally:
        if 'server' in locals():
            server.close()

def shutdown_proxy(signal_received, frame):
    logging.info("Shutting down proxy...")
    sys.exit(0)

if __name__ == "__main__":
    # Configuration
    LISTEN_IP = "0.0.0.0"  # Listen on all interfaces
    LISTEN_PORT = 8080      # Port to listen on
    TARGET_IP = "192.168.2.50"  # Target device IP
    TARGET_PORT = 80        # Target device port
    PROTOCOL = "tcp"        # Protocol: "tcp" or "udp"

    # Handle graceful shutdown
    signal.signal(signal.SIGINT, shutdown_proxy)

    # Start the proxy
    start_proxy(LISTEN_IP, LISTEN_PORT, TARGET_IP, TARGET_PORT, PROTOCOL)