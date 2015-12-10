from threading import Thread, Lock, Timer
import Queue
import SocketServer
from calendar import EntrySet
agent = None
ips = open('ip', 'r').read().split("\n")[0:4]


class ElectionTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        data = json.loads(data)
        global agent
        if agent:
            agent.lock.aquire()
            agent.receive_vote(data)
            agent.lock.release()
        


class AgentUDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        data = json.loads(data)
        global agent
        global ips
        if agent:
            agent.lock.acquire()
            if birthday in data:
                agent.birthdays[data['id']] = data['birthday']
                agent.last_heartbeat[data['id']] = time.time()
            else:
                agent.receive(data)
            agent.lock.release()
    

#For this implemntation, the learner and proposer are the same.     

class Agent():
    leader = 0
    lock = Lock()
    birthdays = []
    last_heartbeat = []
    votes = []
    def check_heartbeat(self):
        if (time.time() - self.last_heartbeat[self.leader]) >= 5:
            self.elect_leader()

    heartbeat_checker = Timer(10, check_heartbeat)
    listener = SocketServer.UDPServer(('0.0.0.0', 6001), AgentUDPHandler)
    election_listener = SocketServer.TCPServer(('0.0.0.0', 6099), ElectionTCPHandler)
    thread = Thread(target = listener.serve_forever)
    thread_election = Thread(target = election_listener.serve_forever)
    selfnode = None
    
    
    def elect_leader(self):
        if (self.votes == []):
            self.votes = [0] * len(self.last_heartbeat)
        global ips
        min_bday = 1000000000000000
        min_bday_id = 0
        i = 0
        for birthday in self.birthdays:
            if birthday < min_bday:
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
                socket.close()
            
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
            if (self.self.node.id == mVotesId):
                self.become_leader()
    
    def become_leader(self):
        pass
            
        
        

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
        self.acceptors = acceptors
        self.selfnode = selfnode
        self.votes = [0] * len(ips)
        self.n = self.selfnode.id
        self.heartbeat_checker.start()
        self.birthdays = [0] * len(ips)
        self.thread.start()
        self.thread_election.start()
        self.birthday = time.time()
        self.ticker = Timer(5, self.tick)
        
        if calendar:
            self.calendar = EntrySet.load(calendar)
    
    def tick(self):
        if (activeValue == None and len(self.values) > 0):
            data = {'event':self.values[0], 'hash' : self.calendar.entry_set.hash, 'type' : 'event'}
            self.receive(json.dumps(data))
            
    
    def receive(self, data):
        global ips

        data = json.loads(data)
        if data['type'] == 'event':
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
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        self.heartbeat_checker.start()

    def receive(self, data):
        if data['type'] == 'prepare':

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
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.sendto(message, (_id, port))
        
    def become_leader(self):
        global ips 
        
        heartbeat_checker.stop()
        listener.shutdown()
        listener.server_close()
        election_listener.shutdown()
        election_listener.close()
        acceptors = []
        global agent
        i = 0
        for ip in ips:
            if i != self.id:
                acceptors.append(i)
        p = Proposer(self.selfnode, acceptors, self.selfnode.entry_set)
        agent = p
        
    
            