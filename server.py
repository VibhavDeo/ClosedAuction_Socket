#Server

import socket
import sys
import threading
import time
import re

class Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.lock = threading.Lock()
        self.auction_status = 0
        self.auction_type = 0

    def start(self):
        self.server_socket.bind(("127.0.0.1", 12345))
        self.server_socket.listen(5)

        print("Server started, waiting for clients...")

        while True:
            client_socket, address = self.server_socket.accept()
            print("Client connected: {}".format(address))
            client_socket.send(("START AUCTION").encode())
            print('in start while')
            data = client_socket.recv(1024).decode()            
            print('in start while')
            print(data)
            print(data.split())

            if data.startswith("START AUCTION"):
                print('in start auction')
                try:
                    print('try')
                    with self.lock:
                        print('lock')
                        self.start_auction(client_socket, str(data))
                except Exception as e:
                    print('Error:', e)
                    client_socket.close()
                    print("Client disconnected: {}".format(address))

            elif data.startswith("BID"):
                try:
                    with self.lock:
                        self.bid(client_socket, data)
                except Exception as e:
                    print('Error:', e)
                    client_socket.close()
                    print("Client disconnected: {}".format(address))

            else:
                client_socket.close()
                print("Client disconnected: {}".format(address))

        self.server_socket.close()

    def start_auction(self, client_socket, data):
        if self.auction_status == 0:
            self.auction_status = 1
            self.auction_type = int(data.split()[2])
            ##VD
            print(self.auction_type)
            ##VD
            self.lowest_price = int(data.split()[3])
            self.number_of_bids = int(data.split()[4])
            self.item_name = ' '.join(data.split()[5:])
            self.bids = {}

            self.auction_thread = threading.Thread(target=self.run_auction, args=(client_socket,))
            self.auction_thread.start()

            client_socket.send(("Auction request received: START AUCTION {} {} {}".format(self.lowest_price, self.number_of_bids, self.item_name)).encode())

        else:
            client_socket.send("Server busy!".encode())
            client_socket.close()

    def bid(self, client_socket, data):
        if self.auction_status == 1:
            bid = int(data.split()[1])

            if bid >= self.lowest_price:
                client_socket.send("Bid received. Please wait...".encode())
                self.bids[client_socket] = bid
            else:
                client_socket.send("Invalid bid. Please submit a positive integer!".encode())
                self.bid(client_socket, data)

        else:
            client_socket.send("Bidding on-going!".encode())
            client_socket.close()

    def run_auction(self, client_socket):
        for i in range(self.number_of_bids - 1):
            print('in for')
            data = client_socket.recv(1024).decode()
            print(data)

            if data.startswith("BID"):
                try:
                    with self.lock:
                        self.bid(client_socket, data)
                except Exception as e:
                    print('Error:', e)
                    client_socket.close()
                    print("Client disconnected: {}".format(client_socket.getpeername()))
            else:
                client_socket.close()
                print("Client disconnected: {}".format(client_socket.getpeername()))

        self.auction_status = 0
        #self.auction_thread.join()

        highest_bid = -1
        highest_bid_socket = None

        for socket, bid in self.bids.items():
            if bid > highest_bid:
                highest_bid = bid
                highest_bid_socket = socket

        second_highest_bid = -1
        second_highest_bid_socket = None

        for socket, bid in self.bids.items():
            if socket != highest_bid_socket and bid > second_highest_bid:
                second_highest_bid = bid
                second_highest_bid_socket = socket

        if highest_bid >= self.lowest_price:
            if self.auction_type == 1:
                client_socket.send(("Auction result: item sold for {} dollars".format(highest_bid)).encode())
                highest_bid_socket.send(("Auction result: you won the auction and now have a payment due of {} dollars".format(highest_bid)).encode())

                for socket, bid in self.bids.items():
                    if socket != highest_bid_socket:
                        socket.send(("Auction result: unfortunately, you did not win in this auction".format(highest_bid)).encode())

            elif self.auction_type == 2:
                client_socket.send(("Auction result: item sold for {} dollars".format(second_highest_bid)).encode())
                highest_bid_socket.send(("Auction result: you won the auction and now have a payment due of {} dollars".format(second_highest_bid)).encode())

                for socket, bid in self.bids.items():
                    if socket != highest_bid_socket:
                        socket.send(("Auction result: unfortunately, you did not win in this auction".format(second_highest_bid)).encode())

        else:
            client_socket.send(("Auction result: unfortunately, your item was not sold in the auction".format(self.lowest_price)).encode())

            for socket, bid in self.bids.items():
                socket.send(("Auction result: unfortunately, you did not win in this auction".format(self.lowest_price)).encode())

        for socket, bid in self.bids.items():
            socket.close()


server = Server()
server.start()