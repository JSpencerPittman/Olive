from pathlib import Path


class Graph(object):
    def __init__(self):
        self._graph = {}

    @property
    def num_nodes(self) -> int:
        return len(self._graph)

    def add_edge(self, src: int, tgt: int, choice: int):
        assert src in self._graph
        self._graph[src].append((tgt, choice))

    def add_node(self) -> int:
        self._graph[self.num_nodes] = []
        return self.num_nodes - 1

    def write(self, path: Path):
        with open(path, "w") as outfile:
            for i in range(self.num_nodes):
                outfile.write(f"{i:<5d}: {self._graph[i]}\n")
