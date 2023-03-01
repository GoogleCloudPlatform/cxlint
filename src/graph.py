"""Utility class for manaing graph structure."""

# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections

class Graph(collections.UserList):
    """Utility class for manaing graph structure."""
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
