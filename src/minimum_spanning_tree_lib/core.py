"""Minimum spanning tree computation via Kruskal's algorithm.

Design notes
------------

* The graph is represented as a list of :class:`Edge` records rather than an
  adjacency structure.  Kruskal's algorithm only ever needs to iterate over
  the edges in non-decreasing weight order, so an adjacency map would be pure
  overhead.

* Weights are compared with the built-in ``<`` operator on whatever numeric
  type the caller supplies (``int`` or ``float``).  We never do arithmetic on
  two weights, so integer weights stay exact instead of being coerced to
  float.  ``total_weight`` is the only place that adds, and it starts from
  ``0`` so that an empty graph sums to ``0`` rather than ``0.0`` when all
  weights are integers.

* The disjoint-set structure uses union by size with path compression.  Union
  by size (rather than by rank) keeps the invariant simple: ``size`` is always
  the number of elements in the tree rooted at that node, which is also handy
  for debugging.

* Vertices are arbitrary hashable objects.  The disjoint set stores them in a
  plain ``dict``; a vertex that is never used as an edge endpoint simply never
  appears.  This means an isolated vertex is invisible to ``kruskal_mst``: a
  forest of one vertex has no edges, and the function returns ``[]``.
"""

from __future__ import annotations

from typing import Dict, Hashable, Iterable, List, Optional, Tuple


class Edge:
    """An undirected, weighted edge between two vertices.

    The edge is undirected: ``Edge('a', 'b', 3)`` and ``Edge('b', 'a', 3)``
    describe the same connection.  We keep the endpoints in the order given so
    that a round-trip through the data structure preserves the caller's input
    order, which makes debugging output and tests predictable.
    """

    __slots__ = ("u", "v", "weight")

    def __init__(self, u: Hashable, v: Hashable, weight) -> None:
        self.u = u
        self.v = v
        self.weight = weight

    def __repr__(self) -> str:
        return "Edge({!r}, {!r}, {!r})".format(self.u, self.v, self.weight)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        return (
            self.u == other.u
            and self.v == other.v
            and self.weight == other.weight
        )

    def __hash__(self) -> int:
        return hash((self.u, self.v, self.weight))


class DisjointSet:
    """Union-find over hashable elements with path compression.

    Elements are created lazily: calling :meth:`find` on an unknown element
    makes it a singleton set.  This is what lets ``kruskal_mst`` accept an
    edge list without a separate vertex enumeration step.
    """

    __slots__ = ("_parent", "_size")

    def __init__(self, elements: Optional[Iterable[Hashable]] = None) -> None:
        self._parent: Dict[Hashable, Hashable] = {}
        self._size: Dict[Hashable, int] = {}
        if elements is not None:
            for element in elements:
                self.add(element)

    def add(self, element: Hashable) -> None:
        """Register ``element`` as its own singleton set if it is new."""
        if element not in self._parent:
            self._parent[element] = element
            self._size[element] = 1

    def find(self, element: Hashable) -> Hashable:
        """Return the representative of ``element``'s set, creating it if new."""
        self.add(element)
        # Iterative two-pass path compression.  Recursion would be simpler but
        # can blow the stack on adversarial inputs (a long chain), and this is
        # a library that may be handed untrusted data.
        root = element
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[element] != root:
            parent = self._parent[element]
            self._parent[element] = root
            element = parent
        return root

    def union(self, a: Hashable, b: Hashable) -> bool:
        """Merge the sets containing ``a`` and ``b``.

        Returns ``True`` when the two elements were in different sets (so a
        merge happened) and ``False`` when they were already connected.  That
        return value is exactly the predicate Kruskal's algorithm needs.
        """
        root_a = self.find(a)
        root_b = self.find(b)
        if root_a == root_b:
            return False
        # Attach the smaller tree under the larger one.
        if self._size[root_a] < self._size[root_b]:
            root_a, root_b = root_b, root_a
        self._parent[root_b] = root_a
        self._size[root_a] += self._size[root_b]
        return True

    def connected(self, a: Hashable, b: Hashable) -> bool:
        """Return whether ``a`` and ``b`` are in the same set."""
        return self.find(a) == self.find(b)

    def num_sets(self) -> int:
        """Return the number of disjoint sets currently tracked."""
        return sum(1 for node, parent in self._parent.items() if node == parent)


# Sorting key used by kruskal_mst.  We sort on weight alone and rely on
# Python's stable sort to preserve input order for ties.  Sorting on the
# endpoints as a tie-breaker would be wrong for mixed-type vertices (e.g. an
# int and a str), which Python 3 refuses to order.
def _weight_key(edge: Edge):
    return edge.weight


def kruskal_mst(edges: Iterable[Edge]) -> List[Edge]:
    """Return a minimum-weight spanning forest for the given edges.

    The result is a list of edges that connects each connected component of
    the input graph with minimum total weight.  If the input is connected the
    result is a spanning tree with ``n - 1`` edges for ``n`` vertices; if it is
    not, the result is a spanning forest with one tree per component.

    Self-loops (``u == v``) are silently dropped: they can never be part of a
    spanning forest, and the disjoint-set union would report them as already
    connected anyway, so dropping them explicitly makes the intent clear.

    Parallel edges are allowed and handled naturally: the heavier of two
    parallel edges is rejected once the lighter one has connected its
    endpoints.

    The input is not mutated.  Edge weights must be mutually comparable with
    ``<`` and must form a total order; mixing incomparable weight types (say
    ``int`` and ``str``) raises ``TypeError`` from the sort, which is the
    caller's bug, not ours to paper over.
    """
    ordered = sorted(edges, key=_weight_key)
    forest = DisjointSet()
    result: List[Edge] = []
    for edge in ordered:
        if edge.u == edge.v:
            continue
        if forest.union(edge.u, edge.v):
            result.append(edge)
    return result


def total_weight(edges: Iterable[Edge]):
    """Return the sum of the weights of ``edges``.

    Starts from the integer ``0`` so that an empty iterable sums to ``0`` and
    integer weights keep their exact type.  Mixing ``int`` and ``float``
    weights promotes to ``float`` as usual.
    """
    total = 0
    for edge in edges:
        total += edge.weight
    return total
