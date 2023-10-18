# auc_server.py
# Author: Vibhav Sunil Deo
# ID: 200537706
# UnityID: vdeo
# Date: 10/12/2023

import socket
import threading
import sys

class AuctionServer:

    def __init__(self):
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

    def start_listening(self):
        print("Auctioneer is ready to host auctions!")
        while True:
            if self.round_reset_flag == 0:
                client_socket, client_address = self.auction_socket.accept()
                client_socket.send("Connected to the Auctioneer server".encode())

                if self.round_reset_flag == 1:
                    self.reset_round()

                if self.auction_status == 0:
                    self.auction_status = 1
                    self.seller_socket, self.seller_address = client_socket, client_address
                    print('Seller connected from ' + str(self.seller_address[0]) + ':' + str(self.seller_address[1]))
                    threading.Thread(target=self.handle_seller_request,args=(self.seller_socket,)).start()

                elif self.auction_status == 1 and not self.bidders:
                    client_socket.send("Server is busy. Try to connect again later. Waiting for the seller.".encode())
                    continue

                if self.auction_status == 5:
                    client_socket.send("Server is busy. Try to connect again later. Bidding in progress".encode())
                    continue

                if len(self.bidders) < self.num_bids:
                    self.bidders.append(client_socket)
                    threading.Thread(target=self.handle_bidder,args=(client_socket,)).start()
                    print(f'Buyer {len(self.bidders)} is connected from ' + str(self.seller_address[0]) + ':' + str(self.seller_address[1]))

                if len(self.bidders) == self.num_bids and len(self.bidders) != 0:
                    print('Requested number of bidders arrived. Let\'s start bidding!')
                    threading.Thread(target=self.handle_auction,args=()).start()
                    print(">> New bidding thread spawned")
                    self.auction_status = 5
                    continue

    def handle_seller_request(self, seller_socket):
        print(">> New seller thread spawned")
        seller_socket.send("seller".encode())
        seller_socket.send("Please submit an auction request: ".encode())

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

    def handle_bidder(self, bidder_socket):
        bidder_socket.send('buyer'.encode())
        if len(self.bidders) < self.num_bids:
            bidder_socket.send('The auctioneer is still waiting for other buyers to connect...'.encode())

    def handle_auction(self):
        bids = {}
        unsold_flag = 0

        for i, bidder in enumerate(self.bidders):
            bidder.send('The bidding has started!\nPlease submit your bid:'.encode())

            while True:
                try:
                    bid = int(bidder.recv(1024).decode())
                    if bid < 1:
                        raise ValueError
                    break
                except ValueError:
                    bidder.send('Server: Invalid bid. Please submit a positive integer!'.encode())

            bids[bidder] = bid
            print(f"Buyer {i + 1} bid ${bid}")
            bidder.send('Server: Bid received. Please wait...'.encode())

        highest_bidder = max(bids, key=bids.get)
        highest_bid = bids[highest_bidder]

        if highest_bid < self.minimum_price:
            unsold_flag = 1
            self.handle_unsuccessful_auction()

        else:
            self.handle_successful_auction(highest_bidder, highest_bid, bids)
            highest_bidder.close()

        if unsold_flag == 0:
            if self.auction_type == 1:
                print("Item Sold! The highest bid is $", self.payments[0], ".")
            elif self.auction_type == 2:
                print("Item Sold! The highest bid is $", self.payments[0], ". The actual bid is $", self.payments[1])

        self.round_reset_flag = 1
        self.seller_socket.close()
        print("Auctioneer is ready to host auctions!")

    def handle_successful_auction(self, highest_bidder, highest_bid, bids):
        if self.auction_type==1:
            self.seller_socket.send(
                (f'Auction Finished!\nYour item {self.item_name} has been sold for ${highest_bid}.\n'
                 f'Disconnecting from the Auctioneer server. Auction is over!').encode())

            highest_bidder.send(
                (f'Auction Finished!\nYou won the item {self.item_name}. Your payment due is ${highest_bid}.\n'
                 f'Disconnecting from the Auctioneer server. Auction is over!').encode())

            for buyer in self.bidders:
                if buyer != highest_bidder:
                    buyer.send(
                        (f'Auction Finished!\nUnfortunately you did not win the last round.\n'
                         f'Disconnecting from the Auctioneer server. Auction is Over!').encode())
                    buyer.close()
            self.payments = [highest_bid]
        if self.auction_type==2:
        
            del bids[highest_bidder]

            second_highest_bidder = max(bids, key=bids.get)
            second_highest_bid = bids[second_highest_bidder]
            self.seller_socket.send(
                (f'Auction Finished!\nYour item {self.item_name} has been sold for ${second_highest_bid}.\n'
                 f'Disconnecting from the Auctioneer server. Auction is over!').encode())

            highest_bidder.send(
                (f'Auction Finished!\nYou won the item {self.item_name}. Your payment due is ${second_highest_bid}.\n'
                 f'Disconnecting from the Auctioneer server. Auction is over!').encode())

            for buyer in self.bidders:
                if buyer != highest_bidder:
                    buyer.send(
                        (f'Auction Finished!\nUnfortunately you did not win the last round.\n'
                         f'Disconnecting from the Auctioneer server. Auction is Over!').encode())
                    buyer.close()
            self.payments = [highest_bid,second_highest_bid]

    def handle_unsuccessful_auction(self):
        self.seller_socket.send('Unfortunately, the item was not sold.'.encode())
        self.seller_socket.close()

        for buyer in self.bidders:
            buyer.send('Auction Finished!\nUnfortunately, you did not win the last round.\n''Disconnecting from the Auctioneer server. Auction is over!'.encode())
            buyer.close()

    def reset_round(self):
        self.auction_status = 0
        self.round_reset_flag = 0
        self.bidders = []
        self.auction_type = 0
        self.minimum_price = 0
        self.num_bids = 0
        self.item_name = ""
        self.payments = []

if __name__ == '__main__':
    auction = AuctionServer()
    auction.start_listening()
