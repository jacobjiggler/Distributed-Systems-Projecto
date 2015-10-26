import SocketServer
from threading import Thread, Lock
from sys import argv
import sys
from calendar import *
from time_table import *
import socket
import time
import calendar
import os

from event import Event, MessageTypes

node = None

class MyTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global node
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "got some information"
        node.lock.acquire()
        if node:
            node.receive(self.data)
        node.lock.release()

class Node():
    ips = []
    def __init__(self, _id):
        self.id = int(_id)
        self.ip = Node.ips[self.id]
        self.lock = Lock()
        self.listener = SocketServer.TCPServer(('0.0.0.0', 6000), MyTCPHandler)
        self.listener.node = self
        self.thread = Thread(target = self.listener.serve_forever)
        self.thread.start()
        self.entry_set = calendar.EntrySet()
        self.init_calendar()
        self.log = open("log.dat", "a+")
        self.last = None

        if os.path.isfile("log.dat"):
            self.entry_set.create_from_log(self)


    def init_calendar(self):
        self.table = TimeTable(len(Node.ips))
        self.events = []

    def kill():
        print('killin')
        self.listener.shutdown()

    # Expect data in the form:
    # {'table': <serialized table>, 'events': <array of events>}
    def receive(self, raw):
        data = json.loads(raw)
        print(self.table.table)
        print(data)
        if data['type'] == "failure":
            self.rec_failure(data)
        else:
            new_table = TimeTable.load(json.loads(data['table']), len(Node.ips))
            events = data['events']

            new_events =[]
            for event in events:
                event = Event.load(json.loads(event))
                if event.entry:
                    event.entry = Entry.load(event.entry)
                new_events.append(event)

            # For all events this node doesn't have, make modifications
            for event in new_events:
                if not self.has_event(event, self.id):
                    res = event.apply(self.entry_set, self)
                    if res:
                        self.events.append(event)
                    else:
                        if event.type == MessageTypes.Insert:
                            self.send_failure(event)

            self.table.sync(new_table, self.id, data['node_id'])
        print(self.table.table)

    def send(self, _id, event=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            data = "data"
           # print("Sending Data from client")
            # Connect to server and send data
            sock.settimeout(3)
            sock.connect((Node.ips[_id], 6000))
            sock.sendall(event)

            # Receive data from the server and shut down
            received = sock.recv(1024)
            # Add To EntrySet
        except:
            print "asdfsdf"
            # Node Down cancel conflict
            if not event == None:
                d = json.loads(event)
                dd = json.loads(d['events'][0])
                event = Event.load(dd)
                event.entry = Entry.load(event.entry)
                print event.entry
                event.type = MessageTypes.Delete
                test = event.apply(self.entry_set, self)
                self.events.append(event)
            pass

        finally:
            sock.close()

    def send_failure(self, event):
        #grab id from event

        print("Sending Failure command")
        data = {
            'node_id': self.id,
            'type': 'failure',
            'event': event.to_JSON()
        }

        self.send(event.node, json.dumps(data))

    def rec_failure(self, data):
        event = Event.load(json.loads(data['event']))
        event.entry = Entry.load(event.entry)

        self.delete_entry(event.entry)

    # Check if a node has a certain event
    def has_event(self,event, node_id):
        return self.table.get(node_id, event.node) >= event.time

    def send_to_node(self, node_id):
        # Don't send anything if the node is this
        if node_id == self.id:
            return

        partial = []
        for event in self.events:
            if not isinstance(event, Event):
                continue
            if not self.has_event(event, node_id):
                partial.append(event.to_JSON())

        data = {
            'type': 'sync',
            'node_id': self.id,
            'table': self.table.to_JSON(),
            'events': partial,
        }

        self.send(node_id, json.dumps(data))

    def add_entry(self, entry):
        event = Event(MessageTypes.Insert, time.time(), self.id, entry)
        self.table.update(self.id, time.time() + 0.1)
        event.apply(self.entry_set, self)
        self.events.append(event)

        for id in entry.participants:
            if not id == self.id:
                self.send_to_node(id)

    def delete_entry(self, entry):
        event = Event(MessageTypes.Delete, time.time(), self.id, entry)
        self.table.update(self.id, time.time() + 0.1)
        event.apply(self.entry_set, self)
        self.events.append(event)

        for id in entry.participants:
            if not id == self.id:
                self.send_to_node(id)

    def kill_thread(self):
        self.thread.terminate()

def main():
    global node
    Node.ips = open('ip', 'r').read().split("\n")[0:4]
    node_id = int(argv[1])
    node = Node(node_id)
    if (len(argv) == 2):
        while True:
            print "[v] View Appointments"
            print "[a] Add Appointment"
            print "[d] Delete Appointment"
            print "[q] Quit Application"

            resp = raw_input("Choice: ").lower()
            if resp == 'v':
                print node.entry_set.__repr__()

            elif resp == 'a':
                part = map(int, raw_input("Node Ids of participants (comma seperated): ").split(","))
                nam = raw_input("Event name: ")
                day = raw_input("Day: ")
                _startTime = raw_input("Start Time: ")
                _endTime = raw_input("End Time: ")

                entry = Entry(part, nam, day, _startTime, _endTime)
                node.add_entry(entry)

            elif resp == 'd':
                resp = int(raw_input("Enter Appointment number: "))
                entry = node.entry_set[resp]
                node.delete_entry(entry)
            elif resp == 'q':
                #node.kill_thread()
                sys.exit(0)

if __name__ == "__main__":
    main()
