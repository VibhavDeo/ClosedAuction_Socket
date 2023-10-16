import socket
import threading

def handle_client(client_socket, is_seller, auction_details, clients):
    try:
        # Determine the role of the client (seller or bidder)
        role = "seller" if is_seller else "bidder"
        client_socket.sendall(role.encode())

        if role == "seller":
            # Receive auction details from the seller
            received_details = client_socket.recv(1024).decode().split(',')
            auction_details.extend(received_details)

            print("Auction Details:")
            print(f"Type: {auction_details[0]}")
            print(f"Minimum Price: {auction_details[1]}")
            print(f"Number of Bidders: {auction_details[2]}")
            print(f"Item Name: {auction_details[3]}")

            # Broadcast auction details to bidders
            for bidder_socket in clients[1:]:
                bidder_socket.sendall(",".join(auction_details).encode())

        elif role == "bidder":
            # Bidder receives acknowledgment from the server
            acknowledgment = client_socket.recv(1024).decode()
            print(f"Acknowledgment for bidder: {acknowledgment}")

            # TODO: Implement bid analysis and winner announcement

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the socket
        client_socket.close()

def start_auction_server():
    host = '127.0.0.1'
    port = 5555

    # Create a socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Bind the socket to a specific address and port
        server_socket.bind((host, port))
        
        # Listen for incoming connections
        server_socket.listen()

        print(f"Auction server is listening on {host}:{port}")

        # List to keep track of connected clients
        clients = []

        # List to store auction details
        auction_details = []

        # Variable to track if the seller has connected
        is_seller_connected = False

        while True:
            # Accept incoming connection
            client_socket, client_address = server_socket.accept()
            print(f"Client connected from {client_address}")

            # Add the client socket to the list
            clients.append(client_socket)

            # Start a new thread to handle the client
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, not is_seller_connected, auction_details, clients)
            )
            client_thread.start()

            # Set the seller connected flag after the first seller connects
            if not is_seller_connected:
                is_seller_connected = True

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the server socket
        server_socket.close()

if __name__ == "__main__":
    start_auction_server()
