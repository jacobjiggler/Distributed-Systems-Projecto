# Enum to represent the different types of messages
class MessageTypes:
    Insert, Delete = range(2)

class Event:
    def __init__(self, typ, time, node, entry):
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

    def apply(entry_set):
        raise Exception("Event is an abstract base")

class Insert(Event):
    def apply(entry_set):
        return entries.add(entry)

class Delete(Event):
    def apply(entry_set):
        return entries.delete(entry)

