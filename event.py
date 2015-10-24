# Enum to represent the different types of messages
class MessageTypes:
    Insert, Delete = range(2)

class Event:
    def __init__(self, typ, time, node):
        self.type = typ
        self.time = time
        self.node = node

def has_record(events, table, node_id, event):
    return table.get(node_id, event.node) >= event.time

def send_to_node(events, table, node_id):
    partial = []
    for event in events:
        if not has_record(events,  table, node_id, event)
            partial.append(event)
