import SocketServer
from threading import Thread
from sys import argv
from calendar import *
from time_table import *
import socket
node = None

class MyTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        if node:
            node.receive(self.data)

class Node():
    ips = []
    def __init__(self, _id):
        self.id = _id
        self.ip = Node.ips[self.id]
        
        listener = SocketServer.TCPServer((self.ip, 6000), MyTCPHandler)
        self.thread = Thread(target = listener.serve_forever)
        self.thread.start()

    def init_calendar(self):
        self.table = TimeTable(1)
        self.events = []

    def receive(self, data):
        #do things with raw datums
        print "Received Data"
        print data

    def send(self, _id):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            data = "data"
            print "Sending Data from client"
            # Connect to server and send data
            sock.connect((Node.ips[_id], 6000))
            sock.sendall(data + "\n")

            # Receive data from the server and shut down
            received = sock.recv(1024)
            # Add To EntrySet
        except : 
            pass
            # Node Down cancel conflict
        finally:
            sock.close()

    # Check if a node has a certain event
    def has_event(event, node_id):
        return self.table.get(node_id, event.node) >= event.time

    def send_to_node(node_id):
        partial = []
        for event in self.events:
            if not self.has_event(event, node_id)
                partial.append(event)

if __name__ == "__main__":
    Node.ips = open('ip', 'r').read().split("\n")[0:4]
    node = Node(argv[1])

