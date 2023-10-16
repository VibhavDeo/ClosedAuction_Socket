import socket

def start_client():
    host = '127.0.0.1'
    port = 5555

    # Create a socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client_socket.connect((host, port))
        print(f"Connected to the auction server at {host}:{port}")

        # Determine if the client is a seller or bidder
        role = client_socket.recv(1024).decode()
        print(role)
        if role == 'seller':
            # Seller submits auction details
            auction_type = input("Enter the type of auction: ")
            min_price = input("Enter the minimum price: ")
            num_bidders = input("Enter the number of bidders: ")
            item_name = input("Enter the item name: ")

            # Send auction details to the server
            auction_details = f"{auction_type},{min_price},{num_bidders},{item_name}"
            client_socket.sendall(auction_details.encode())
        elif role == 'bidder':
            # Receive auction details from the server
            auction_details = client_socket.recv(1024).decode().split(',')
            auction_type, min_price, num_bidders, item_name = auction_details

            print("Auction Details:")
            print(f"Type: {auction_type}")
            print(f"Minimum Price: {min_price}")
            print(f"Number of Bidders: {num_bidders}")
            print(f"Item Name: {item_name}")

            # Bidder submits a bid
            bid = input("Enter your bid: ")
            client_socket.sendall(bid.encode())

            # Receive acknowledgment from the server
            acknowledgment = client_socket.recv(1024).decode()
            print(f"Acknowledgment from server: {acknowledgment}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the socket
        client_socket.close()

if __name__ == "__main__":
    start_client()
