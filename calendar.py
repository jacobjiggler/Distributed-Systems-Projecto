import time
import datetime

class Entry():    
    def __init__(self, participants, name, day, start):
        self.participants = participants
        self.name = name
        self.day = day
        self.start = start
        
    def __repr__(self):
        return "Entry(%s, %s, %s, %s)" % (self.participants, self.name, self.day, self.start)
    def __eq__(self, other):
        if isinstance(other, Item):
            return ((self.participants == other.participants) and (self.name == other.name) and (self.day == other.day) and (self.start == other.start))
        else:
            return False
    def __ne__(self, other):
        return (not self.__eq__(other))
    def __lt__(self, other):
        return 
    def __hash__(self):
        return hash(self.__repr__())
        
        
