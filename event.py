import json
# Enum to represent the different types of messages
class MessageTypes:
    Insert, Delete = range(2)

class Event:
    log = None
    def __init__(self, typ=None, time=None, node=None, entry=None):
        self.type = typ
        self.time = time
        self.node = node
        self.entry = entry

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True)

    @staticmethod
    def load(js):
        a = Event()
        a.__dict__ = js
        return a

    def apply(self, entry_set):
        if log:
            log.write(self.to_JSON() + "\n")
            print self.to_JSON()
        if self.type == MessageTypes.Insert:
            return entry_set.add(self.entry)
        elif self.type == MessageTypes.Delete:
            return entry_set.delete(self.entry)

        raise Exception("Event was not one of the types")
