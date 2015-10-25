import json

# A class to represent the time table's held by each node
class TimeTable(object):
    log = None
    def __init__(self, dim=None):
        self.dim = dim
        self.init_table()

    def init_table(self):
        self.table = []
        for _ in range(self.dim):
            self.table.append([0] * self.dim)

    # When syncing with a new node, just update all of our clock times to
    # the max of both tables
    def sync(self, t2):
        assert len(t2) == len(self.table)

        for i in range(self.dim):
            for j in range(self.dim):
                self.table[i][j] = max(self.table[i][j], t3[i][j])

    # Call this when a node performs a local "insert" or "delete" operation
    def update(self, node, count):
        self.table[node][node] = count

    def get(self, i, j):
        return self.table[i][j]

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True)

    @staticmethod
    def load(js):
        a = TimeTable()
        a.__dict__ = js
        return a
