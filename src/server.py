"""
@Author: Vibhav Sunil Deo
@Date: 10/12/2023

auc_server.py: This file handles the auctioneer

Usage: python3 auc_server.py <PORT>
"""

import socket
import threading
import sys
import time

"""Auctioneer class"""
class AuctionServer:

    """Initialize class variables"""
    def __init__(self):
        #initializing variables
        #self.server_ip = socket.gethostbyname(socket.gethostname())
        self.server_ip = '127.0.0.1'

        self.server_port = int(sys.argv[1])
        self.auction_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.auction_socket.bind((self.server_ip, self.server_port))
        self.auction_socket.listen()
        self.auction_status = 0
        self.round_reset_flag = 0
        self.bidders = []
        self.auction_type = 0
        self.minimum_price = 0
        self.num_bids = 0
        self.item_name = ""
        self.payments = []

    """Reset class variables for next auction"""
    def reset_round(self):
        #reinitialize class variables for next auction
        self.auction_status = 0
        self.round_reset_flag = 0
        self.bidders = []
        self.auction_type = 0
        self.minimum_price = 0
        self.num_bids = 0
        self.item_name = ""
        self.payments = []

    """Method to handle communication for successful auction. (max bid price >= minimum_price)"""
    def handle_successful_auction(self, highest_bidder, highest_bid, bids, minimum_price):
        #for auction type =1 ; first-price
        if self.auction_type==1:
            
            #send auction result to seller
            self.seller_socket.send(('Auction Finished!\nYour item '+str(self.item_name)+' has been sold for $'+str(highest_bid)+'.\nDisconnecting from the Auctioneer server. Auction is over!').encode())

            #send auction result to auction winner
            highest_bidder.send(('Auction Finished!\nYou won the item '+str(self.item_name)+' Your payment due is $'+str(highest_bid)+'.\nDisconnecting from the Auctioneer server. Auction is over!').encode())

            #send auction result to other bidders
            for buyer in self.bidders:
                if buyer != highest_bidder:
                    buyer.send(('Auction Finished!\nUnfortunately you did not win the last round.\nDisconnecting from the Auctioneer server. Auction is Over!').encode())
                    buyer.close()
            self.payments = [highest_bid]

        #for auction type =1 ; second-price
        if self.auction_type==2:
            
            #sfinding the second highest bid
            del bids[highest_bidder]
            second_highest_bidder = max(bids, key=bids.get)
            second_highest_bid = bids[second_highest_bidder]

            #Case to handle the minimum selling price of the item
            if minimum_price>second_highest_bid:
                second_highest_bid=minimum_price

            #send auction result to seller
            self.seller_socket.send(('Auction Finished!\nYour item '+str(self.item_name)+' has been sold for $'+str(second_highest_bid)+'.\nDisconnecting from the Auctioneer server. Auction is over!').encode())

            #send auction result to highest bidder
            highest_bidder.send(('Auction Finished!\nYou won the item '+str(self.item_name)+'. Your payment due is $'+str(second_highest_bid)+'.\nDisconnecting from the Auctioneer server. Auction is over!').encode())

            #send auction result to other bidders
            for buyer in self.bidders:
                if buyer != highest_bidder:
                    buyer.send(('Auction Finished!\nUnfortunately you did not win the last round.\nDisconnecting from the Auctioneer server. Auction is Over!').encode())
                    buyer.close()
            self.payments = [highest_bid,second_highest_bid]

    """Method to handle communication for unsuccessful auction. (max bid price < minimum_price)"""
    def handle_unsuccessful_auction(self):

        #send auction result to seller
        self.seller_socket.send('Unfortunately, the item was not sold.'.encode())
        self.seller_socket.close()

        #send auction result to all the bidders
        for buyer in self.bidders:
            buyer.send('Auction Finished!\nUnfortunately, you did not win the last round.\n''Disconnecting from the Auctioneer server. Auction is over!'.encode())
            buyer.close()

    """This method manages all the incoming connections from client. setting them as seller/buyer, allowing clients to join."""
    def start_listening(self):
        print("Auctioneer is ready to host auctions!")

        #continuously listen for incoming users
        while True:
            
            #accept incoming client side connections
            client_socket, client_address = self.auction_socket.accept()
            client_socket.send("Connected to the Auctioneer server".encode())

            #if previous auction has been completed, reset flag is set to 1. calls reset_round function
            if self.round_reset_flag == 1:
                self.reset_round()

            #condition to accept first connection as a seller
            if self.auction_status == 0:
                self.auction_status = 1
                self.seller_socket, self.seller_address = client_socket, client_address
                print('Seller connected from ' + str(self.seller_address[0]) + ':' + str(self.seller_address[1]))
                threading.Thread(target=self.handle_seller_request,args=(self.seller_socket,)).start()

            #condition to handle incoming connection when seller is giving inputs
            elif self.auction_status == 1 and not self.bidders:
                client_socket.send("Server is busy. Try to connect again later. Waiting for the seller.".encode())
                continue
            
            #case to handle new bidders joining after max bidders reached
            if self.auction_status == 5:
                client_socket.send("Server is busy. Try to connect again later. Bidding in progress".encode())
                continue
            
            #case to handle adding new bidders until buyers number is reached
            if len(self.bidders) < self.num_bids:
                self.bidders.append(client_socket)
                threading.Thread(target=self.handle_bidder,args=(client_socket,)).start()
                print('Buyer '+str(len(self.bidders))+' is connected from ' + str(client_address[0]) + ':' + str(client_address[1]))

            #case to start auction after all bidders have joined
            if len(self.bidders) == self.num_bids and len(self.bidders) != 0:
                print('Requested number of bidders arrived. Let\'s start bidding!')
                threading.Thread(target=self.handle_auction,args=()).start()
                print(">> New bidding thread spawned")
                self.auction_status = 5
                continue
    
    """This method fetches sellers request"""
    def handle_seller_request(self, seller_socket):
        print(">> New seller thread spawned")

        #sending role to client as 'seller'
        seller_socket.send("seller".encode())
        seller_socket.send("Please submit an auction request: ".encode())

        #fetching auction item details until valid details are obtained
        while True:
            try:
                auction_request = seller_socket.recv(1024).decode()
                self.auction_type, self.minimum_price, self.num_bids, self.item_name = auction_request.split()
                self.auction_type, self.minimum_price, self.num_bids = int(self.auction_type), int(self.minimum_price), int(self.num_bids)

                if self.auction_type not in [1, 2]:
                    raise ValueError

                seller_socket.send("Server: Auction Start".encode())
                print("Auction request received. Now waiting for buyers...")
                self.auction_status = 2
                break

            except ValueError:
                seller_socket.send('Invalid auction request!\nPlease submit an auction request: '.encode())

    """This method ahndles bidder connections"""
    def handle_bidder(self, bidder_socket):
        #sending role to client as 'buyer'
        bidder_socket.send('buyer'.encode())

        #sending message to existing bidders to wait for others to connect
        if len(self.bidders) <= self.num_bids:
            bidder_socket.send('The auctioneer is still waiting for other buyers to connect...'.encode())

    """This method handle bids from the connected bidders in the ongoing auction"""
    def handle_bids(self,bids):
        #Fetch bids from all the buyers
        for i, bidder in enumerate(self.bidders):
            time.sleep(2)
            bidder.send('The bidding has started!\nPlease submit your bid:'.encode())

            #fetching bid amount from buyers until valid bid is obtained
            while True:
                try:
                    bid = int(bidder.recv(1024).decode())
                    if bid < 1:
                        raise ValueError
                    break
                except ValueError:
                    bidder.send('Server: Invalid bid. Please submit a positive integer!'.encode())

            bids[bidder] = bid
            print('Buyer '+str(i + 1)+' bid $'+str(bid))
            bidder.send('Server: Bid received. Please wait...'.encode())

    """This method handles auction process, determining if the item is sold and finding the winner"""
    def handle_auction(self):
        bids = {}
        unsold_flag = 0

        self.handle_bids(bids)

        #fecth higest bidder and bid amount from the list
        highest_bidder = max(bids, key=bids.get)
        highest_bid = bids[highest_bidder]

        #if max bid amount is less than minimum seller price, the item remains unsold. calling method to handle the case
        if highest_bid < self.minimum_price:
            unsold_flag = 1
            self.handle_unsuccessful_auction()

        #mthod to handle the auction when item gets sold
        else:
            self.handle_successful_auction(highest_bidder, highest_bid, bids,self.minimum_price)
            print("TEST_HIGHEST_BIDDER:",highest_bidder.getpeername())
            highest_bidder.close()

        #when item gets sold, display the result
        if unsold_flag == 0:
            if self.auction_type == 1:
                print("Item Sold! The highest bid is $", self.payments[0], ".")
            elif self.auction_type == 2:
                print("Item Sold! The highest bid is $", self.payments[0], ". The actual bid is $", self.payments[1])

        #set reset flag to 1 to indicate that the  auction is over and close seller socket
        self.round_reset_flag = 1
        print("TEST_SELLER:",self.seller_socket.getpeername())
        self.seller_socket.close()

        print("Auctioneer is ready to host auctions!")

if __name__ == '__main__':
    auction = AuctionServer()
    auction.start_listening()
