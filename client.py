#Client

import socket
import sys
import time
import re

class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.socket.connect((self.server_ip, self.server_port))
        print('client start 0')
        data = self.socket.recv(1024).decode()
        print(data)
        print('client start')
        if data.startswith("START AUCTION"):
            print('b4 start auction')
            self.start_auction()
            print('after start auction')
        elif data.startswith("BIDDING START"):
            #if data.startswith("BIDDING START"):
            self.bid()

        else:
            self.socket.close()

    def start_auction(self):
        print('in start aution')
        auction_type = input("Enter 1 for first-price auction, or 2 for second-price auction: ")
        lowest_price = input("Enter the lowest price you are willing to sell for: ")
        number_of_bids = input("Enter the number of bids you are willing to accept: ")
        item_name = input("Enter the name of the item to be sold: ")

        self.socket.send(("START AUCTION {} {} {} {}".format(auction_type, lowest_price, number_of_bids, item_name)).encode())

        data = self.socket.recv(1024).decode()
        print(data)

        if data.startswith("Auction request received"):
            data = self.socket.recv(1024).decode()
            print(data)

            if data.startswith("Bidding start"):
                while True:
                    try:
                        data = self.socket.recv(1024).decode()
                        print(data)
                    except Exception as e:
                        print('Error:', e)
                        break

    def bid(self):
        bid = input("Enter your bid: ")

        self.socket.send(("BID {}".format(bid)).encode())

        data = self.socket.recv(1024).decode()
        print(data)

        if data.startswith("Bid received"):
            while True:
                try:
                    data = self.socket.recv(1024).decode()
                    print(data)
                except Exception as e:
                    print('Error:', e)
                    break


if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        print("Usage: python3 {} <server_ip> <server_port>".format(sys.argv[0]))
        exit()

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    client = Client(server_ip, server_port)
    client.start()