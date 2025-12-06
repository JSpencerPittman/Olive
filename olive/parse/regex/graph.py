from pathlib import Path
from typing import Optional
from copy import copy


EMPTY_WEIGHT = -1
ANY_WEIGHT = -2


class Graph(object):
    def __init__(self):
        self._graph = {}
        self._start_node = -1
        self._end_node = -1

    @property
    def num_nodes(self) -> int:
        return len(self._graph)

    @property
    def start_node(self) -> Optional[int]:
        return None if self._start_node == -1 else self._start_node

    def add_edge(self, src: int, tgt: int, weight: int):
        assert src in self._graph
        self._graph[src].append((tgt, weight))

    def add_node(self) -> int:
        self._graph[self.num_nodes] = []
        return self.num_nodes - 1

    def mark_start_node(self, node: int):
        assert node in self._graph
        self._start_node = node

    def mark_end_node(self, node: int):
        assert node in self._graph
        self._end_node = node

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

    def step(self, step: int):
        self._prev_frontier = copy(self._frontier)
        self._can_revert = True
        self._take_step(step)
        self._find_zero_weight_neighborhood()

    def revert_step(self):
        assert self._can_revert
        self._frontier = self._prev_frontier
        self._prev_frontier = None
        self._can_revert = False

    def valid_so_far(self) -> bool:
        return len(self._frontier) > 0

    def is_finished(self) -> bool:
        for node in self._frontier:
            if node == self._graph._end_node:
                return True
        return False

    def reset(self):
        self._frontier = set([self._graph.start_node])
        self._find_zero_weight_neighborhood()

        self._prev_frontier = None
        self._can_revert = False

    def _find_zero_weight_neighborhood(self):
        expansion = copy(set(self._frontier))
        frontier = copy(set(self._frontier))
        explored = set()

        while len(frontier):
            node = frontier.pop()
            explored.add(node)
            for neighbor, w in self._graph.outgoing_edges(node):
                if w == EMPTY_WEIGHT and neighbor not in explored:
                    frontier.add(neighbor)
                    expansion.add(neighbor)

        self._frontier = expansion

    def _take_step(self, weight: int):
        expansion = set()
        expansion_any = set()

        for node in self._frontier:
            for neighbor, w in self._graph.outgoing_edges(node):
                if w == weight:
                    expansion.add(neighbor)
                if w == ANY_WEIGHT:
                    expansion_any.add(neighbor)

        self._frontier = expansion if len(expansion) else expansion_any
