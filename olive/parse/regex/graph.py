class Graph(object):
    def __init__(self):
        self._edges = {}

    def add_edge(self, u: int, v: int):
        if u in self._edges:
            self._edges[u].append(v)
        else:
            self._edges[u] = []
