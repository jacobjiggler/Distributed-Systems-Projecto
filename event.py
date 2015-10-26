import json

from calendar import Entry

# Enum to represent the different types of messages
class MessageTypes:
    Insert, Delete = range(2)

class Event:
    def __init__(self, typ=None, time=None, node=None, entry=None):
        self.type = typ
        self.time = time
        self.node = node
        self.entry = entry

    def dicttester(self, o):
        if hasattr(o, 'thread'):
            return o.id
        if hasattr(o, '__dict__'):
            return o.__dict__
        else:
            return None

    def to_JSON(self):
        return json.dumps(self, default=lambda o: self.dicttester(o),
            sort_keys=True)

    @staticmethod
    def load(js):
        a = Event()
        a.__dict__ = js
        return a

    def apply(self, entry_set, node):
        if node.log and not node.log.closed and not self == node.last:
            node.log.write(self.to_JSON() + "\n")
            node.log.flush()
        node.last = self
        if self.type == MessageTypes.Insert:
            return entry_set.add(self.entry)
        elif self.type == MessageTypes.Delete:
            return entry_set.delete(self.entry)

        raise Exception("Event was not one of the types")
