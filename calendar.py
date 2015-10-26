import time
import datetime
import json

class Entry():
    def __init__(self, participants=None, name = None, day=None, start=None, end=None):
        self.participants = participants
        self.name = name
        self.day = day
        self.start = start
        self.end = end

    def __repr__(self):
        return "Participants: %s, Name: %s, Day: %s, Time: %s - %s" % (self.participants, self.name, self.day, self.start, self.end)
    def __eq__(self, other):
        if isinstance(other, Entry):
            return ((self.participants == other.participants) and (self.name == other.name) and (self.day == other.day) and (self.start == other.start) and (self.end == other.end))
        else:
            return False
    def __ne__(self, other):
        return (not self.__eq__(other))
    def __hash__(self):
        return hash(self.__repr__())

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True)

    def is_valid(self, entry):
        if self.day != entry.day:
            return True
        else:
            caltime1 = self.start.split(':')
            caltime2 = self.end.split(':')
            entime1 = entry.start.split(':')
            entime2 = entry.end.split(':')
            c1 = int(caltime1[0])*60 + int(caltime1[1])
            c2 = int(caltime2[0])*60 + int(caltime2[1])
            e1 = int(entime1[0])*60 + int(entime1[1]) + 1
            e2 = int(entime2[0])*60 + int(entime2[1]) - 1
            if e1 > c1 and e1 < c2:
                return False
            if e2 > c1 and e2 < c2:
                return False
            else:
                return True

    @staticmethod
    def load(js):
        a = Entry()
        a.__dict__ = js
        return a

class EntrySet():
    def __init__(self):
        self.calendar = []

    def __repr__(self):
        strs = map(str, self.calendar)
        for i in xrange(0, len(strs)):
            strs[i] = "[" + str(i) + "] " + strs[i]
        return '\n'.join(strs)

    def __getitem__(self, key):
        return self.calendar[key]


    #log file exists with entries
    def create_from_log(self):
        self.calendar = []

        #create calendar from it
        #using log file

    def add(self, entry):
        valid = True
        for existing_entry in self.calendar:
            if not entry.is_valid(existing_entry):
                valid = False
                print "scheduling conflict"
        if entry in self.calendar or not valid:
            return False
        else:
            self.calendar.append(entry)
            return True

    def delete(self, entry):
        if entry in self.calendar:
            self.calendar.remove(entry)
            return True
        else:
            return False

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True)

    @staticmethod
    def load(js):
        a = EntrySet()
        a.__dict__ = js
        return a
