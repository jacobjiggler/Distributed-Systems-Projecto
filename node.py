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
import json

import paxos
from threading import Timer

from event import Event, MessageTypes, perpetualTimer

node = None

class NodeUDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global node
        # self.request is the TCP socket connected to the client
        self.data = self.request[0].strip()
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
        self.birthday = time.time()
        
        self.listener = SocketServer.UDPServer(('0.0.0.0', 6000), NodeUDPHandler)
        self.listener.node = self
        self.thread = Thread(target = self.listener.serve_forever)
        self.thread.start()
        
        self.heartbeat_timer = perpetualTimer(3, self.heartbeat)
        self.heartbeat_timer.start()
        
        
        self.entry_set = calendar.EntrySet()
        self.init_calendar()
        self.log = open("log.dat", "a+")
        self.last = None
        
        #first is default leader. If leader goes down, elections occur.

        if os.path.isfile("log.dat"):
            self.entry_set.create_from_log(self)


    def init_calendar(self):
        self.table = TimeTable(len(Node.ips))
        self.events = []

    def kill(self):
        print('killin')
        self.listener.shutdown()
        
    def heartbeat(self):
        if paxos.agent == None:
            return
        for node in Node.ips:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            data = {'birthday':self.birthday, 'nEvents' : len(paxos.agent.events), 'id' : self.id, 'type' : 'heartbeat', 'leader' : paxos.agent.leader}
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(json.dumps(data), (node, 6001))
            sock.sendto(json.dumps(data), (node, 6002))



    # Expect data in the form:
    # {'type' => type, 'calendar' => Entry_Set, 'value' => Entry }
    def receive(self, raw):
        data = json.loads(raw)
        
        if data['type'] == "learn":
            print data['event']
            print json.loads(data['event'])
            event = Event.load(json.loads(data['event']))
            if event.entry and not isinstance(event.entry, Entry):
                if isinstance(event.entry, dict):
                    event.entry = Entry.load(event.entry)
                else:
                    event.entry = Entry.load(json.loads(event.entry))
            if self.id not in event.entry.participants:
                paxos.agent.events.append(event)
                return
            res = event.apply(self.entry_set, self)
            if res:
                paxos.agent.events.append(event)
            
        elif data['type'] == 'sync':
            print data['events']
            events = json.loads(data['events'])
            print events 
            for e in events:
                
                self.receive(json.dumps({ "type" : 'learn', 'event' : e }))


    def send(self, event=None):
        _id = Node.ips[paxos.agent.leader]
        event.me = self.id
        data = {'event':event.to_JSON(),  'type' : 'event'}
        if (paxos.agent.leader == self.id):
            paxos.agent.receive(data)
            return
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        data = {'event':event.to_JSON(), 'hash' : self.entry_set.hash, 'type' : 'event'}
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(json.dumps(data), (_id, 6001))
        sock.close()

    def send_failure(self, event):
        #grab id from event

        print("Sending Failure command")
        data = {
            'node_id': self.id,
            'type': 'failure',
            'event': event.to_JSON()
        }

       # self.send(event.node, json.dumps(data))

    def rec_failure(self, data):
        event = Event.load(json.loads(data['event']))
        event.entry = Entry.load(event.entry)

        self.delete_entry(event.entry)

    # Check if a node has a certain event
    def has_event(self,event, node_id):
        return self.table.get(node_id, event.node) >= event.time


    def add_entry(self, entry, add=True):
        event = Event(MessageTypes.Insert, time.time(), self.id, entry)
        if add:
            self.table.update(self.id, time.time() + 0.1)
            event.apply(self.entry_set, self)
            self.events.append(event)
        
        self.send(event)

    def delete_entry(self, entry, exclude=[], add=True):
        event = Event(MessageTypes.Delete, time.time(), self.id, entry)
        if add:
            self.table.update(self.id, time.time() + 0.1)
            event.apply(self.entry_set, self)
            self.events.append(event)

        self.send(event)

    def kill_thread(self):
        self.thread.terminate()

def main():
    global node
    Node.ips = open('ip', 'r').read().split("\n")[0:5]
    node_id = int(argv[1])
    node = Node(node_id)
    
    if node_id == 0:
        i = 0
        acceptors = []
        for ip in Node.ips:
            if i != node.id:
                acceptors.append(i)
            i += 1
        paxos.agent = paxos.Proposer(node, acceptors)
    else:
        paxos.agent = paxos.Acceptor(node)
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
                part.append(node.id)
                part = list(set(part))
                entry = Entry(part, nam, day, _startTime, _endTime)
                node.add_entry(entry, False)

            elif resp == 'd':
                resp = int(raw_input("Enter Appointment number: "))
                entry = node.entry_set[resp]
                node.delete_entry(entry, [], False)
            elif resp == 'q':
                #node.kill_thread()
                sys.exit(0)

if __name__ == "__main__":
    main()
