# minimum_spanning_tree_lib

Computes a minimum-weight spanning forest of an edge-weighted undirected graph
using Kruskal's algorithm with a disjoint-set (union-find) structure.

## Usage

```python
from minimum_spanning_tree_lib import Edge, kruskal_mst, total_weight

edges = [
    Edge("a", "b", 1),
    Edge("b", "c", 2),
    Edge("a", "c", 3),
]

tree = kruskal_mst(edges)
print(tree)                 # [Edge('a', 'b', 1), Edge('b', 'c', 2)]
print(total_weight(tree))   # 3
```

`kruskal_mst` returns a list of `Edge` objects. If the input graph is
connected, that list is a spanning tree with `n - 1` edges. If it is not, you
get a spanning forest: one minimum tree per connected component.

## Why this exists

The only thing Kruskal's algorithm needs from a graph is a list of edges sorted
by weight, plus a way to ask "are these two vertices already connected?".
Building an adjacency map, a vertex registry, or a graph object first is extra
state to maintain and extra ways for the caller to get it wrong. This library
therefore takes the edge list directly and returns the chosen edges directly.

The trade-off is that there is no graph object to query afterwards: if you want
to ask about an edge that was not selected, you already have the input list, and
if you want the total weight, `total_weight` sums it for you. Vertices are
arbitrary hashable objects, so the same code works for strings, integers, or
tuples.

## The awkward edge

An isolated vertex is invisible. Because the algorithm never enumerates
vertices, a vertex that appears in no edge cannot appear in the result, and
`kruskal_mst([])` returns `[]` rather than a forest of singletons. If you need
those isolated vertices represented, add them to your own bookkeeping; the
library deliberately does not guess at a vertex set you did not supply.

Weights must be mutually comparable with `<` and must form a total order.
Mixing incomparable weight types (for example `int` and `str`) raises
`TypeError` from the sort, which is the caller's bug rather than something to
paper over. `total_weight` starts from the integer `0`, so an empty iterable
sums to `0` and integer weights stay exact until a float weight forces a
promotion.

## Exports

- `Edge(u, v, weight)` — an undirected weighted edge record. Equality and
  hashing are field-for-field, so `Edge("a", "b", 1) != Edge("b", "a", 1)`;
  the undirectedness is a property of the algorithm, not of the record.
- `DisjointSet(elements=None)` — union-find with path compression and union by
  size. `find`, `union`, `connected`, `add`, and `num_sets` are available;
  `union` returns `True` when a merge actually happened.
- `kruskal_mst(edges)` — returns the list of edges in the minimum spanning
  forest. Self-loops are dropped, parallel edges are handled, and the input
  iterable is not mutated.
- `total_weight(edges)` — sums the weights of an iterable of edges.
