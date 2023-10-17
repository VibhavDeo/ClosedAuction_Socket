# Mohammed Sami Ashfak MK (mamk)

# Importing the required libraries
import socket
import sys
# Client configuration
HOST = sys.argv[1]
PORT = int(sys.argv[2])


def seller_mode(seller_socket): 
    auctioneer_response = seller_socket.recv(1024).decode()
    print(auctioneer_response)
    while True:
        bidding_information = input()
        seller_socket.send(bidding_information.encode())
        auctioneer_response = seller_socket.recv(1024).decode()
        print(auctioneer_response)
        if "Server: Auction Start" in auctioneer_response:
            break

    
    auctioneer_response = seller_socket.recv(1024).decode()
    print(auctioneer_response)
    

def buyer_mode(buyer_socket):
    while True:
        auctioneer_response = buyer_socket.recv(1024).decode()
        print(auctioneer_response)
        if "The bidding has started!" in auctioneer_response:
            break
    
    while True: 
        bidding_offer = input()
        buyer_socket.send(str(bidding_offer).encode())
        auctioneer_response = buyer_socket.recv(1024).decode()
        if "Server: Bid received. Please wait..." in auctioneer_response:
            break
    
    auctioneer_response = buyer_socket.recv(1024).decode()
    print(auctioneer_response)


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    server_response = client_socket.recv(1024).decode()
    print(server_response)
    server_response = client_socket.recv(1024).decode()
    if "Server is busy. Try to connect again later." in server_response:
            print(server_response)
            client_socket.close()
            return
         
    if server_response == 'seller':
        print("Your role is: [Seller]")
        seller_mode(client_socket)
    elif server_response == 'buyer':
        print("Your role is: [Buyer]")
        buyer_mode(client_socket)
        


if __name__ == '__main__':
    main()
