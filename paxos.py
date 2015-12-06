from threading import Thread, Lock
import queue
proposer = None
acceptor = None
learner = None
leader = None
ips = open('ip', 'r').read().split("\n")[0:4]

class NodeUDPHandler(SocketServer.BaseRequestHandler):
    pass

class AgentUDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        # self.request is the TCP socket connected to the client
        data = self.request.recv(1024).strip()
        data = json.loads(data)
        t = data['to']
        global proposer
        global acceptor
        agent = None
        if t == 'proposer':
            agent = proposer
        elif t == 'acceptor':
            agent = acceptor
        elif t == 'learner'
            agent == learner
        if agent:
            agent.lock.acquire()
                agent.receive(data)
            agent.lock.release()
    

#For this implemntation, the learner and proposer are the same.     

class Proposer():
    isLeader = True
    selfnode = None
    values = set()
    activeNegiation = False
    activeValue = None
    acceptors = []
    nodes = []
    lock = Lock()
    n = 1
    maxReceived = {}
    nPromise = 0
    listener = SocketServer.UDPServer(('0.0.0.0', 6001), AgentUDPHandler)
    
    def __init__(self,  selfnode, acceptors, nodes):
        self.acceptors = acceptors
        self.selfnode = selfnode
        self.nodes = nodes
        self.n = self.selfnodes.id
        
    def receive(self, data):
        if data['type'] == 'event':
            #check timestamp stuff
            self.values.add(data['value'])
            if self.activeNegiation == True:
                continue
            self.activeValue = data['value']
            data = {
                'type': 'prepare',
                'from': self.id,
                'n': n,
            }
            
            for acceptor in self.acceptors:
                self.send(acceptor, json.dumps(data))
            n += len(self.nodes) + 1
            
        elif data['type'] == 'promise':
            if data['responce'] = 'reject'
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
                    self.send(acceptor, json.dumps(sdata))
                    
            elif data['type'] == 'accepted':
                if data['responce'] = 'reject':
                    reset()
                    return
                if self.nAccepted >= len(self.acceptors)/2:
                    sdata = {
                        'type' : 'learn',
                        'value' : self.activeValue
                    }
                    self.node.receive(sdata)
                    for node in self.nodes:
                        self.send(node, json.dumps(sdata))
                        
                    values.discard(self.activeValue)
                    reset()
            
    def reset(self):
        pass
        
    def send(self, _id, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(message, (_id, UDP_PORT))


class Acceptor():
    selfnode = None
    maxN = 0
    maxProposal = None
    proposals = {}
    promise = 0
    leader = None
    listener = SocketServer.UDPServer(('0.0.0.0', 6001), AgentUDPHandler)
    lock = Lock()
    
    def receive(self, data):
        if data['type'] == 'prepare':

            if data['n'] < promise:
                data = {
                    'type': 'promise',
                    'responce': 'reject',
                    'n': data['n'],
                }
                self.send(data['from'], json.dumps(data))
                return
            
                

            _data = {
                'type': 'promise',
                'responce' : 'promise',
                'from': self.selfnode.id,
                'proposals' : maxProposal,
                'n': data['n'],
            }
            
            self.send(data['from'], json.dumps(_data))
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
            self.send(learner, json.dumps(sdata))
            
    def send(self, _id, message):
        global ips
        _id = ips[_id]
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(message, (_id, 6001))
                    
