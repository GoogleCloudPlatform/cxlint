import collections

class Graph(collections.UserList):
    def __init__(self):
        self._nodes = set()
        self._edges = collections.defaultdict(list)
        self._used_nodes = set()

    def add_node(self, node):
        """Add node to set of all nodes, regardless of use in graph."""
        self._nodes.add(node)

    def add_edge(self, node1, node2):
        self._edges[node1].append(node2)

    def add_used_node(self, node):
        """Add node to set of active in use nodes for the graph."""
        self._used_nodes.add(node)

    def remove_node(self, node):
        self._nodes.remove(node)

    def remove_edge(self, node1, node2):
        self._edges[node1].remove(node2)

    def __str__(self):
        return f"Graph({self._nodes}, {self._edges})"
