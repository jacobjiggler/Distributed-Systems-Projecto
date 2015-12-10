from threading import Thread, Lock, Timer
import Queue
import SocketServer
from calendar import EntrySet
import time
import socket
import json
from event import perpetualTimer
agent = None
ips = open('ip', 'r').read().split("\n")[0:5]


class ElectionTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        data = json.loads(data)
        global agent
        print "Received TCP: " + str(data)
        if agent:
            agent.lock.acquire()
            agent.receive_vote(data['vote'])
            agent.lock.release()
        


class AgentUDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        data = json.loads(data)
        if not 'birthday' in data:
            print "Received UDP: " + str(data)
        global agent
        global ips
        if agent:
            agent.lock.acquire()
            if 'birthday' in data:
                agent.birthdays[data['id']] = float(data['birthday'])
                agent.last_heartbeat[data['id']] = time.time()
                
                if agent.leader != data['leader']:
                    agent.nDiffleader += 1
                    if agent.nDiffleader >= len(agent.votes)/2:
                        agent.leader = data['leader']
                        nDiffleader = 0
            else:
                agent.receive(data)
            agent.lock.release()
    

#For this implemntation, the learner and proposer are the same.     

class Agent():
    leader = 0
    nDiffleader = 0
    lock = Lock()
    birthdays = []
    last_heartbeat = []
    votes = []
    def check_heartbeat(self):
        self.last_heartbeat[self.selfnode.id] = time.time()
        if self.leader == self.selfnode.id:
            return
        if (time.time() - self.last_heartbeat[self.leader]) >= 7.5:
            print "tdiff:" + str(time.time() - self.last_heartbeat[self.leader])
            self.elect_leader()

    selfnode = None
    
    
    def elect_leader(self):
        print 'changing leader'
        if (self.votes == []):
            self.votes = [0] * len(self.last_heartbeat)
        global ips
        min_bday = 1000000000000000
        min_bday_id = 0
        i = 0
        for birthday in self.birthdays:
            if birthday < min_bday and (time.time() - self.last_heartbeat[i]) >= 7.5:
                min_bday = birthday
                min_bday_id = i
            i +=1
        
        for ip in ips:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                data = {'vote' : min_bday_id}
                sock.settimeout(3)
                sock.connect((ip, 6099))
                sock.sendall(json.dumps(data))
                # Add To EntrySet
            except:
                # Node Down cancel conflict
                pass
            finally:
                sock.close()
            
    def receive_vote(self, vote):
        self.votes[vote] += 1
        nVotes = 0
        maxVotes = 0
        mVotesId = 0
        i = 0
        for vote in self.votes:
            nVotes += vote
            if vote > maxVotes:
                maxVotes = vote
                mVotesId = i
            i += 1
        
        if nVotes == len(self.votes) - 2:
            self.leader = mVotesId
            if hasattr(self, 'acceptors'):
                del self.acceptors[mVotesId]
            if (self.selfnode.id == mVotesId and self.selfnode.id != self.leader):
                self.become_leader()
    
            
        
        

class Proposer(Agent):
    isLeader = True
    selfnode = None
    values = set()
    activeNegiation = False
    activeValue = None
    acceptors = []
    n = 1
    leader = 0
    maxReceived = {}
    nPromise = 0
    calendar = None
    birthdays = []
    birthday = 0
    last_heartbeat = []
    
    def __init__(self,  selfnode, acceptors, calendar=None):
        global ips
        self.listener = SocketServer.UDPServer(('0.0.0.0', 6001), AgentUDPHandler)
        self.election_listener = SocketServer.TCPServer(('0.0.0.0', 6099), ElectionTCPHandler)
        self.thread = Thread(target = self.listener.serve_forever)
        self.thread_election = Thread(target = self.election_listener.serve_forever)
        self.thread.start()
        self.thread_election.start()
        
        self.acceptors = acceptors
        self.selfnode = selfnode
        self.votes = [0] * len(ips)
        self.n = self.selfnode.id
        self.last_heartbeat = [time.time()] * 5
        self.heartbeat_checker = perpetualTimer(8, self.check_heartbeat)
        self.heartbeat_checker.start()
        self.birthdays = [0] * len(ips)
        self.thread.start()
        self.thread_election.start()
        self.birthday = time.time()
        self.ticker = perpetualTimer(5, self.tick)
        self.ticker.start()
        
        if calendar:
            self.calendar = EntrySet.load(calendar)
    
    def tick(self):
        self.last_heartbeat[self.selfnode.id] = time.time()
        if (activeValue == None and len(self.values) > 0):
            data = {'event':self.values[0], 'hash' : self.calendar.entry_set.hash, 'type' : 'event'}
            self.receive(json.dumps(data))
            
    
    def receive(self, data):
        global ips
        
        data = json.loads(data)
        print 'received: ' + str(data)
        if data['type'] == 'event':
            print "Event: "
            if self.calendar.entry_set.hash != data['hash']:
                sdata = {
                    'type' : 'sync',
                    'calendar' : self.calendar.toJSON()
                }
                self.send(data['from'], json.dumps(sdata), 6000)
            if (data['value'] not in self.values):
                self.values.add(data['value'])
            if self.activeNegiation == True:
                return
            self.activeValue = data['value']
            data = {
                'type': 'prepare',
                'from': self.id,
                'n': n,
            }
            
            for acceptor in self.acceptors:
                self.send(acceptor, json.dumps(data), 6002)
            n += len(ips) + 1
            
        elif data['type'] == 'promise':
            if data['responce'] == 'reject':
                reset()
                return
            proposal = json.loads(data['proposals'])
            if not proposal == []:
                if not self.maxReceived == {} and proposal[0] > self.maxReceived[0]:
                    maxReceived = proposal
            self.nPromise += 1
            if self.nPromise >= len(self.acceptors)/2:
                value = self.activeValue
                if not self.maxReceived == {}:
                    self.activeValue = self.maxReceived
                sdata = {
                    'type': 'accept',
                    'from': self.id,
                    'n': data['n'],
                    'value' : json.dumps(self.activeValue)
                }
                for acceptor in self.acceptors:
                    self.send(acceptor, json.dumps(sdata), 6002)
                    
            elif data['type'] == 'accepted':
                if data['responce'] == 'reject':
                    reset()
                    return
                if self.nAccepted >= len(self.acceptors)/2:
                    if not self.isLeader:
                        data['type'] = 'learn'
                        self.send(leader, data, 6001)
                    event = Event.load(json.loads(self.activeValue))
                    if event.entry:
                        event.entry = Entry.load(event.entry)
                    if not self.node.entry_set.check(event.entry):
                        values.discard(self.activeValue)
                        reset()
                        
                    d = json.dumps({'type' : 'learn' ,'event': event.to_JSON()})
                    for node in ips:
                        self.send(node, d, 6000)
                        #will this work to self?
                    values.discard(self.activeValue)
                    self.calendar.add(event)
                    reset()
            
    def reset(self):
        self.activeNegiation = False
        self.activeValue = None
        self.maxReceived = {}
        
    def send(self, _id, port=6002, message= ""):
        global ips
        _id = ips[_id]
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(message, (_id, port))
    
    def become_leader(self):
        self.isLeader = True
        



class Acceptor(Agent):
    selfnode = None
    maxN = 0
    maxProposal = None
    proposals = {}
    promise = 0
    leader = 0               #change back to 1
    lock = Lock()
    
    
    
    def __init__(self, selfnode):
        global ips
        self.birthdays = [0] * len(ips)
        self.selfnode = selfnode
        self.last_heartbeat = [0] * 5
        self.heartbeat_checker = perpetualTimer(10, self.check_heartbeat)
        self.listener = SocketServer.UDPServer(('0.0.0.0', 6002), AgentUDPHandler)
        self.election_listener = SocketServer.TCPServer(('0.0.0.0', 6099), ElectionTCPHandler)
        self.thread = Thread(target = self.listener.serve_forever)
        self.thread_election = Thread(target = self.election_listener.serve_forever)
        self.thread.start()
        self.thread_election.start()
        self.heartbeat_checker.start()
        self.votes = [0] * 5

    def receive(self, data):
        print 'received (accept): ' + str(data)
        if data['type'] == 'prepare':
            print 'prepare: '
            if data['n'] < promise:
                data = {
                    'type': 'promise',
                    'responce': 'reject',
                    'n': data['n'],
                }
                self.send(data['from'], json.dumps(data), 6001)
                return
            
                

            _data = {
                'type': 'promise',
                'responce' : 'promise',
                'from': self.selfnode.id,
                'proposals' : maxProposal,
                'n': data['n'],
            }
            
            self.send(data['from'], json.dumps(_data), 6001)
            promise = data['n']

            
            
        elif data['type'] == 'accept':
            print 'accept'
            if self.promise > data['n']:
                sdata = {
                    'type': 'accepted',
                    'from': self.selfnode.id,
                    'n': data['n'],
                    'responce' : 'reject'
                    }
                self.send(data['from'], json.dumps(sdata) )
            
            sdata = {
                'type': 'accepted',
                'from': self.id,
                'n': data['n']
            }
            self.send(leader, json.dumps(sdata))
            
    def send(self, _id, message, port=6001):
        global ips
        _id = ips[_id]
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(message, (_id, port))
        
    def become_leader(self):
        global ips 
        print 'becoming leader'
        self.heartbeat_checker.close()
        self.listener.shutdown()
        self.listener.server_close()
        self.election_listener.shutdown()
        self.election_listener.close()
        self.acceptors = []
        global agent
        i = 0
        for ip in ips:
            if i != self.id:
                acceptors.append(i)
        p = Proposer(self.selfnode, acceptors, self.selfnode.entry_set)
        agent = p
        
    
            
