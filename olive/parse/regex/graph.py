from pathlib import Path
from typing import Optional
from copy import copy


class Graph(object):
    def __init__(self):
        self._graph = {}
        self._start_node = -1
        self._associations = {}

    @property
    def num_nodes(self) -> int:
        return len(self._graph)

    @property
    def start_node(self) -> Optional[int]:
        return None if self._start_node == -1 else self._start_node

    def add_edge(self, src: int, tgt: int, weight: int, priority: int):
        assert src in self._graph
        self._graph[src].append((tgt, weight, priority))

    def add_node(self) -> int:
        self._graph[self.num_nodes] = []
        return self.num_nodes - 1

    def mark_start_node(self, node: int):
        assert node in self._graph
        self._start_node = node

    def mark_node_association(self, node: int, assoc: int, priority: int):
        assert node in self._graph
        self._associations[node] = (assoc, priority)

    def outgoing_edges(self, node: int, priority: int) -> list[tuple[int, int]]:
        assert node in self._graph
        return [(src, tgt) for src, tgt, p in self._graph[node] if priority >= p]

    def association(self, node: int, rule_priority: int) -> Optional[int]:
        if node in self._associations and self._associations[node][1] == rule_priority:
            return self._associations[node][0]
        return None

    def write(self, path: Path):
        with open(path, "w") as outfile:
            for i in range(self.num_nodes):
                outfile.write(f"{i:<5d}: {self._graph[i]}\n")


class GraphTraveler(object):
    def __init__(self, graph: Graph, num_rules: int):
        self._graph = graph
        self._num_rules = num_rules
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
        for rule_idx in range(self._num_rules):
            if len(self._frontier[rule_idx]):
                return True
        return False

    def reached_symbols(self) -> Optional[int]:
        assocs = []
        for rule_priority, rule_frontier in enumerate(self._frontier):
            for node in rule_frontier:
                if (assoc := self._graph.association(node, rule_priority)) is not None:
                    assocs.append((node, rule_priority, assoc))

        if len(assocs) > 1:
            """
            Return the most specific association. In this context the association with the fewest
            outgoing edges is considered the most specific.
            """
            return sorted(
                assocs, key=lambda assoc: len(self._graph.outgoing_edges(*assoc[:2]))
            )[0][2]
        elif len(assocs) == 1:
            return assocs[0][2]

        return None

    def reset(self):
        self._frontier = [
            set([self._graph.start_node]) for idx in range(self._num_rules)
        ]
        self._find_zero_weight_neighborhood()

        self._prev_frontier = None
        self._can_revert = False

    def _find_zero_weight_neighborhood(self):
        def is_empty_edge(weight: int) -> bool:
            return weight == -1

        for rule_pri in range(self._num_rules):
            expansion = copy(set(self._frontier[rule_pri]))
            frontier = copy(set(self._frontier[rule_pri]))
            explored = set()

            while len(frontier):
                node = frontier.pop()
                explored.add(node)
                for neighbor, w in self._graph.outgoing_edges(node, rule_pri):
                    if is_empty_edge(w) and neighbor not in explored:
                        frontier.add(neighbor)
                        expansion.add(neighbor)

            self._frontier[rule_pri] = expansion

    def _take_step(self, weight: int):
        for rule_pri in range(self._num_rules):
            expansion = set()
            explored = set()

            for node in self._frontier[rule_pri]:
                explored.add(node)
                for neighbor, w in self._graph.outgoing_edges(node, rule_pri):
                    if w == weight and neighbor not in explored:
                        expansion.add(neighbor)

            self._frontier[rule_pri] = expansion
