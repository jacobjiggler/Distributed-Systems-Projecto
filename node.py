import SocketServer
from threading import Thread
from sys import argv
from calendar import *
from time_table import *
import socket
import time
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
        if os.path.isfile("log.dat"):
            self.entry_set.create_from_log()
        self.log = open("log.txt", "a")
        listener = SocketServer.TCPServer((self.ip, 6000), MyTCPHandler)
        self.thread = Thread(target = listener.serve_forever)
        self.thread.start()
        self.entry_set = calendar.EntrySet()





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
            new_table = TimeTable.load(json.loads(data['table']))
            events = data['events']

            new_events =[]
            for event in events:
                new_events.append( Event.load(json.loads(event) ))

            # For all events this node doesn't have, make modifications
            for event in new_events:
                if not self.has_event(event, self.id):
                    res = event.apply(self.entry_set)
                    if res:
                        self.events.append(event)
                        data = {
                            'events': [event.to_JSON()],
                        }
                        log.write(json.dumps(data))
                    elif event.type == MessageTypes.Insert:
                        send_failure(event)


            self.table.sync(new_table)


    def send(self, _id, event=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            data = "data"
            print("Sending Data from client")
            # Connect to server and send data
            sock.connect((Node.ips[_id], 6000))
            sock.sendall(data + "\n")

            # Receive data from the server and shut down
            received = sock.recv(1024)
            # Add To EntrySet
        except:
            # Node Down cancel conflict
            if not event == None:
                event.type = MessageTypes.Delete
                event = event.apply(self.entry_set)
                self.events.append(event)
            pass

        finally:
            sock.close()

    def send_failure(self, event):
        #grab id from event

        print("Sending Failure command")
        data = {
            'type': 'failure',
            'event': event.to_JSON()
        }
        json.dumps(data)
    def rec_failure(self, data):
        data = json.loads(data)
        event = Event.load(json.loads(data['event']))

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

        self.send(json.dumps(data))

if __name__ == "__main__":
    Node.ips = open('ip', 'r').read().split("\n")[0:4]
    node = Node(argv[1])
    if (len(argv) == 2):
        print "[v] View Appointments"
        print "[a] Add Appointment"
        print "[d] Delete Appointment"

        resp = raw_input("Choice: ").lower()
        entries = list(node.entry_set)
        if resp == 'v':
            i = 1
            for entry in entries:
                print "" + i + ") " + entry.__repr__()

        elif resp == 'a':
            part = raw_input("Node Ids of participants (comma seperated): ").split(",")
            nam = raw_input("Event name: ")
            day = raw_input("Day: ")
            time = raw_input("Time: ")

            entry = Entry(part, nam, day, time)
            event = Event(Event.MessageType.Insert, time.time(), node, entry)
            data = {
                'table': node.table.to_JSON(),
                'events': [event.to_JSON()],
            }
            node.send(json.dumps(data))


        elif resp == 'd':
            resp = int(raw_input("Enter Appointment number: "))
            entry = node.entries[resp]
            event = Event(Event.MessageType.Delete, time.time(), node, entry)
            data = {
                'table': node.table.to_JSON(),
                'events': [event.to_JSON()],
            }

            node.send(json.dumps(data))
