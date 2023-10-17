# auc_client.py
# Author: Vibhav Sunil Deo
# ID: 200537706
# UnityID: vdeo
# Date: 10/12/2023

import socket
import sys

class AuctionClient:
    def __init__(self, host, port):
        # create IPv4 socket for connecting with server
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.role = None

    def connect_to_server(self):
        #Connecting to the input IP and port
        self.client_socket.connect((self.host, self.port))
        
        #Displaying Connection status recieved from the server
        resp = self.client_socket.recv(1024).decode()
        print(resp)

        #Using the server response to see if there is an auction running with one seller and required number of bidders
        resp = self.client_socket.recv(1024).decode()
        if "Server is busy. Try to connect again later." in resp:
            print(resp)
            self.client_socket.close()
            sys.exit(1)

        #Storing the client type (buyer/seller) recieved from the server
        self.role = resp
        print(f"Your role is: [{self.role}]")

    def start(self):
        #Executing buyer/seller
        if self.role == 'seller':
            self.seller()
        elif self.role == 'buyer':
            self.buyer()

    def seller(self):
        #Server requests for item details from seller
        resp = self.client_socket.recv(1024).decode()
        print(resp)

        #sending auction request to the server. If invalid request is sent, client asks for new item information
        while True:
            bidding_information = input()
            self.client_socket.send(bidding_information.encode())
            auctioneer_response = self.client_socket.recv(1024).decode()
            print(auctioneer_response)

            #If the auction request is valid break the loop
            if "Server: Auction Start" in auctioneer_response:
                break

        #Server sends the acknowledgement of the recieved bid
        auctioneer_response = self.client_socket.recv(1024).decode()
        print(auctioneer_response)

    def buyer(self):
        #Server sends the response that you are the bidder
        #Stays in loop until all buyers are connected
        flag=0
        while True:
            auctioneer_response = self.client_socket.recv(1024).decode()
            print(auctioneer_response)

            #Auction starts when all the buyers have joined the server
            if "The bidding has started!" in auctioneer_response:
                break
            #Case to handle incoming bidders after the auction gets full
            elif "Server is busy. Try to connect again later." in auctioneer_response:
                flag=1
                break
        if flag==0:
            #server accepts the bid from buyer and waits until all the buyers bid
            while True:
                bidding_offer = input()
                self.client_socket.send(str(bidding_offer).encode())
                auctioneer_response = self.client_socket.recv(1024).decode()
                #waits until bids from all buyers are recieved
                if "Server: Bid received. Please wait..." in auctioneer_response:
                    break
                else:
                    print(auctioneer_response)
                    print('Please submit your bid:')

            #server sends the result of the auction
            auctioneer_response = self.client_socket.recv(1024).decode()
            print(auctioneer_response)

    def close_connection(self):
        #closing the socket
        self.client_socket.close()

def main():
    # If the code is given wrong inputs while running exit the code asking for the right inputs
    if len(sys.argv) != 3:
        print("Usage: python script.py <host> <port>")
        sys.exit(1)

    #fetch host and port from the input arguments
    host = sys.argv[1]
    port = int(sys.argv[2])

    #Initialize client and run the client program
    client = AuctionClient(host, port)
    client.connect_to_server()
    client.start()
    client.close_connection()

if __name__ == '__main__':
    main()
