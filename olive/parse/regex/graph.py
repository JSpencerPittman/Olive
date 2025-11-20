from pathlib import Path
from typing import Optional
from copy import copy


class Graph(object):
    def __init__(self):
        self._graph = {}
        self._start_node = -1
        self._end_node = -1
        self._end_node_assoc = -1

    @property
    def num_nodes(self) -> int:
        return len(self._graph)

    @property
    def start_node(self) -> Optional[int]:
        return None if self._start_node == -1 else self._start_node

    @property
    def end_node(self) -> Optional[int]:
        return None if self._end_node == -1 else self._end_node

    @property
    def end_node_assoc(self) -> Optional[int]:
        return None if self._end_node_assoc == -1 else self._end_node_assoc

    def add_edge(self, src: int, tgt: int, choice: int):
        assert src in self._graph
        self._graph[src].append((tgt, choice))

    def add_node(self) -> int:
        self._graph[self.num_nodes] = []
        return self.num_nodes - 1

    def mark_start_node(self, node: int):
        assert node in self._graph
        self._start_node = node

    def mark_end_node(self, node: int, assoc: int):
        assert node in self._graph
        self._end_node = node
        self._end_node_assoc = assoc

    def outgoing_edges(self, node: int) -> list[tuple[int, int]]:
        assert node in self._graph
        return self._graph[node]

    def write(self, path: Path):
        with open(path, "w") as outfile:
            for i in range(self.num_nodes):
                outfile.write(f"{i:<5d}: {self._graph[i]}\n")


class GraphTraveler(object):
    def __init__(self, graph: Graph):
        self._graph = graph
        assert graph.start_node is not None
        self.reset()

    @staticmethod
    def is_empty_edge(weight: int) -> bool:
        return weight == -1

    def step(self, step: int):
        self._take_step(step)
        self._find_zero_weight_neighborhood()

    def valid_so_far(self) -> bool:
        return len(self._frontier) > 0

    def finished(self) -> Optional[tuple[int, int]]:
        assert self._graph.end_node is not None
        for node in self._frontier:
            if node == self._graph.end_node:
                assert self._graph.end_node_assoc is not None
                return node, self._graph.end_node_assoc
        return None

    def reset(self):
        self._frontier = set([self._graph.start_node])
        self._find_zero_weight_neighborhood()

    def _find_zero_weight_neighborhood(self):
        expansion = copy(set(self._frontier))
        frontier = copy(set(self._frontier))
        explored = set()

        while len(frontier):
            node = frontier.pop()
            explored.add(node)
            for neighbor, w in self._graph.outgoing_edges(node):
                if GraphTraveler.is_empty_edge(w) and neighbor not in explored:
                    frontier.add(neighbor)
                    expansion.add(neighbor)

        self._frontier = expansion

    def _take_step(self, weight: int):
        expansion = set()
        explored = set()

        for node in self._frontier:
            explored.add(node)
            for neighbor, w in self._graph.outgoing_edges(node):
                if w == weight and neighbor not in explored:
                    expansion.add(neighbor)

        self._frontier = expansion
