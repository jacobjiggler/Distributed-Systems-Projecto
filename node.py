import SocketServer
from threading import Thread
from sys import argv
from calendar import *
from time_table import *
import socket
import calendar
import os
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
        self.id = int(_id)
        self.ip = Node.ips[self.id]

        listener = SocketServer.TCPServer((self.ip, 6000), MyTCPHandler)
        self.thread = Thread(target = listener.serve_forever)
        self.thread.start()
        self.entry_set = calendar.EntrySet()
        if os.path.isfile("log.dat"):
            self.entry_set.create_from_log()



    def init_calendar(self):
        self.table = TimeTable(1)
        self.events = []

    # Expect data in the form:
    # {'table': <serialized table>, 'events': <array of events>}
    def receive(self, raw):
        # unserialize the data, somehow
        data = json.loads(raw)

        if data['type'] == "failure":
            rec_failure(data)
        else:
            new_table = UNSERIALIZE_TABLE(data['table'])
            new_events = UNSERIALIZE_EVENTS(data['events'])

            # For all events this node doesn't have, make modifications
            for event in new_events:
                if not self.has_event(event, self.id):
                    res = event.apply(self.entry_set)
                    if res:
                        self.events.append(event)
                    elif event.type == MessageTypes.Insert:
                        send_failure(event)
            self.table.sync(new_table)

    def send(self, _id, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print("Sending Data from client")
            # Connect to server and send data
            sock.connect((Node.ips[_id], 6000))
            sock.sendall(data)

            # Receive data from the server and shut down
            received = sock.recv(1024)
            # Add To EntrySet
        except:
            pass
            # Node Down cancel conflict
        finally:
            sock.close()

    def send_failure(self, event):
        dest = Node.ips[event.node]

        print("Sending Failure command")
        data = {
            'type': 'failure',
            'event': event.to_JSON()
        }
        json.dumps(data)
        self.send(dest, data)

    def rec_failure(self, data):
        data = json.loads(data)
        event = Event.load(json.loads(data['event']))

        # create a delete event for this entry
        self.events.append(Event(MessageTypes.Delete, time.time(), self.id, event.entry))

        # Send the delete event to all nodes
        for node_id in Node.ids:
            self.send_to_node(node_id)

    # Check if a node has a certain event
    def has_event(self,event, node_id):
        return self.table.get(node_id, event.node) >= event.time

    def send_to_node(self, node_id):
        partial = []
        for event in self.events:
            if not self.has_event(event, node_id):
                partial.append(event.to_JSON())

        data = {
            'table': self.table.to_JSON(),
            'events': partial,
        }

        self.send(node_id, json.dumps(data))

if __name__ == "__main__":
    Node.ips = open('ip', 'r').read().split("\n")[0:4]
    node = Node(argv[1])
