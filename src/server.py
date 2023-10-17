# auc_server.py
# Author: Vibhav Sunil Deo
# ID: 200537706
# UnityID: vdeo
# Date: 10/12/2023
# v2

import socket
import threading
import sys

class Auctioneer:

    def __init__(self):
        self.HOST = '127.0.0.1'
        self.PORT = int(sys.argv[1])
        self.auctioneer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.auctioneer_socket.bind((self.HOST, self.PORT))
        self.auctioneer_socket.listen()
        self.status = 0
        self.status2 = 0
        self.buyers_list = []
        self.auction_details = {'type_of_auction': 0,'lowest_price': 0,'number_of_bids': 0,'item_name': ""}
        self.payment = []

    def listen(self):
        print("Auctioneer is ready for hosting auctions on PORT:", self.PORT)
        while True:
            #if self.status != 4 and self.status2==0:
            if self.status2==0:
                client_socket, client_address = self.auctioneer_socket.accept()
                client_socket.send("Connected to the Auctioneer server".encode())
                
                #case to handle new round of auction
                if self.status2==1:
                    self.status = 0
                    self.status2 = 0
                    self.buyers_list = []
                    self.auction_details = {'type_of_auction': 0,'lowest_price': 0,'number_of_bids': 0,'item_name': ""}
                    self.payment = []
                    

                #case to add first client as seller
                if self.status == 0:
                    self.status = 1
                    self.seller_socket, self.seller_address = client_socket, client_address
                    print('Seller connected from '+ str(self.seller_address[0])+':'+ str(self.seller_address[1]))
                    threading.Thread(target=self.handle_seller,
                                    args=(self.seller_socket,)).start()

                #case to handle new client joining when seller is connected but bidding has not started yet
                elif self.status == 1 and len(self.buyers_list) == 0:
                    client_socket.send("Server is busy. Try to connect again later. Waiting for seller.".encode())
                    continue

                #case to handle new bidders joining after max bidders reached
                if self.status==5:
                    client_socket.send("Server is busy. Try to connect again later. Bidding in progress".encode())
                    continue

                #case to handle adding new bidders until buyers number is reached
                if len(self.buyers_list) < self.auction_details['number_of_bids']:
                    self.buyers_list.append(client_socket)
                    threading.Thread(target=self.handle_buyer,
                                    args=(client_socket,)).start()
                    print(f'Buyer {len(self.buyers_list)} is connected from '+ str(self.seller_address[0])+':'+ str(self.seller_address[1]))

                #case to start auction after all bidders have joined
                if len(self.buyers_list) == self.auction_details['number_of_bids'] and len(self.buyers_list)!=0:
                    print('Requested number of bidders arrived. Let\'s start bidding!')
                    threading.Thread(target=self.handle_auction,
                                    args=()).start()
                    print(">> New bidding thread spawned")
                    self.status=5
                    continue
                
                
    def handle_seller(self,client_socket):
        # Request the seller to submit an auction request.
        print(">> New seller thread spawned")
        client_socket.send("seller".encode())
        client_socket.send("Please submit an auction request: ".encode())

        while True:
            # Parse the auction request from the seller
            try:
                 # Receive the auction request from the seller
                auction_request = client_socket.recv(1024).decode()
                type_of_auction, lowest_price, number_of_bids, item_name = auction_request.split()
                type_of_auction = int(type_of_auction)
                lowest_price = int(lowest_price)
                number_of_bids = int(number_of_bids)

                if type_of_auction not in [1, 2]:
                    raise ValueError
                # Store all the auction details
                self.auction_details = {
                    'type_of_auction': type_of_auction,
                    'lowest_price': lowest_price,
                    'number_of_bids': number_of_bids,
                    'item_name': item_name
                }

                client_socket.send("Server: Auction Start".encode())
                print("Auction request receieved. Now waiting for buyers...")
                self.status = 2
                break

            except:
                # Let the seller know if the auction request is invalid
                client_socket.send('Invalid auction request!\nPlease submit an auction request: '.encode())

    def handle_buyer(self,client_socket):
        client_socket.send('buyer'.encode())
        if len(self.buyers_list) < self.auction_details['number_of_bids']:
            client_socket.send('The auctioneer is still waiting for other buyer to connect...'.encode())
        # Add the client to the buyers_list
        
       
    def handle_auction(self):
    
        # Dictionary to store the bids
        bids = {}
        unsold_flag = 0

        # Getting bids from all the Buyers
        for i,buyer in enumerate(self.buyers_list):
            buyer.send('The bidding has started!\nPlease submit your bid:'.encode())

            while True:
                try:
                    bid = int(buyer.recv(1024).decode())
                    if bid < 1:
                        raise ValueError
                    break
                except:
                    buyer.send('Server: Invalid bid. Please submit a positive integer!'.encode())
                
            # Storing the bid and the bidder in a dictionary
            bids[buyer] = bid
            print(f"buyer {i+1} bid ${bid}")
            # Informing the Buyer that the bid has been received
            buyer.send('Server: Bid received. Please wait...'.encode())

        # Finding the highest bidder and the highest bid
        highest_bidder = max(bids, key=bids.get)
        highest_bid = bids[highest_bidder]

        # In case of an unsuccessful auction
        if highest_bid < self.auction_details['lowest_price']:
            unsold_flag = 1
            # Inform the seller that item was not sold and close the connection
            self.seller_socket.send('Unfortunately the item was not sold.'.encode())
            self.seller_socket.close()

            # Inform the buyers they did not win the auction and close the connection
            for buyer in self.buyers_list:
                buyer.send('Auction Finished!\nUnfortunately you did not win the last round.\nDisconnecting from the Auctioneer server. Auction is over!'.encode())
                buyer.close()

        # In case of a successful auction find the winners
        else:
            # Finding winners of the first-price auction
            if self.auction_details['type_of_auction'] == 1:

                # Informing the Seller that the item has been sold
                self.seller_socket.send(
                    (f'Auction Finished!\n! Your item {self.auction_details["item_name"]} has been sold for ${highest_bid}.\nDisconnecting from the Auctioneer server. Auction is over!').encode())
            
                # Informing the Buyer who has won the auction
                highest_bidder.send(
                    (f'Auction Finished!\nYou won the item {self.auction_details["item_name"]}. Your payment due is ${highest_bid}.\nDisconnecting from the Auctioneer server. Auction is over!').encode())
                
                for buyer in self.buyers_list:
                    if buyer != highest_bidder:
                        buyer.send(
                            (f'Auction Finished!\nUnfortunately you did not win the last round.\nDisconnecting from the Auctioneer server. Auction is Over!').encode())
                    buyer.close()
                self.payment = [highest_bid]

            elif self.auction_details['type_of_auction'] == 2:
                # Removing highest bid from the dictionary
                del bids[highest_bidder]

                # Finding the second highest bid
                second_highest_bidder = max(bids, key=bids.get)
                second_highest_bid = bids[second_highest_bidder]

                # Informing the Seller that item has been sold
                self.seller_socket.send(
                    (f'Auction Finished!\n! Your item {self.auction_details["item_name"]} has been sold for ${second_highest_bid}.\nDisconnecting from the Auctioneer server. Auction is over!').encode())

                # Informing the Buyer that he has won the auction
                highest_bidder.send(
                    (f'Auction Finished!\n! You won this item {self.auction_details["item_name"]}! Your payment due is ${second_highest_bid}.\nDisconnecting from the Auctioneer server. Auction is over!').encode())

                for buyer in self.buyers_list:
                    if buyer != highest_bidder:
                        buyer.send(
                            (f'Auction Finished!\nUnfortunately you did not win the last round.\nDisconnecting from the Auctioneer server. Auction is over!').encode())
                    buyer.close()
                self.payment = [highest_bid,second_highest_bid]
            highest_bidder.close()
        
        if unsold_flag==0:
            if self.auction_details['type_of_auction'] == 1:
                print("Item Sold! The highest bid is $",self.payment[0],".")
            elif self.auction_details['type_of_auction'] == 2:
                print("Item Sold! The highest bid is $",self.payment[0],".The actual bid is $",self.payment[1])
        
        self.status2 = 1
        self.seller_socket.close()
        print("Auctioneer is ready for hosting auctions on PORT:", self.PORT)
        
if __name__ == '__main__':
    auction = Auctioneer()
    auction.listen()
