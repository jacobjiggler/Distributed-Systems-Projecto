import SocketServer
from threading import Thread
from sys import argv
import socket
node = None

class MyTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()

        self.request.sendall("ACK") #replace with some appropriate responce...
        if node:
            node.receive(self.data)

class Node():
    def __init__(self, ip):
        self.ip = ip
        listener = SocketServer.TCPServer((self.ip, 6000), MyTCPHandler)
        self.thread = Thread(target = listener.serve_forever)
        self.thread.start()

    def receive(self, data):
        #do things with raw datums
        print "Received Data"
        print data

    def send(self, ip):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            data = "data"
            print "Sending Data from client"
            # Connect to server and send data
            sock.connect((ip, 6000))
            sock.sendall(data + "\n")

            # Receive data from the server and shut down
            received = sock.recv(1024)
            print "ACK: " + received
        finally:
            sock.close()


if __name__ == "__main__":
    node = Node(argv[1])
    dic = EntrySet()

