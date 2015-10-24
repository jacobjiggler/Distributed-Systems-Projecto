# Enum to represent the different types of messages
class MessageTypes:
    Insert, Delete = range(2)

class Event:
    def __init__(self, typ, time, node, entry):
        self.type = typ
        self.time = time
        self.node = node
        self.entry = entry

    def apply(entry_set):
        raise Exception("Event is an abstract base")

class Insert(Event):
    def apply(entry_set):
        entries.add(entry)

class Delete(Event):
    def apply(entry_set):
        entries.delete(entry)
