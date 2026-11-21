"""Tests for minimum_spanning_tree_lib.core.

The suite exercises the awkward cases: disconnected graphs, self-loops,
parallel edges, single-vertex components, and non-string hashable vertices.
All assertions are deterministic; no clocks, no randomness, no floats
compared with ``==``.
"""

import unittest

from minimum_spanning_tree_lib import DisjointSet, Edge, kruskal_mst, total_weight


class EdgeTests(unittest.TestCase):
    def test_repr_round_trips_endpoints_and_weight(self):
        edge = Edge("a", "b", 3)
        self.assertEqual(repr(edge), "Edge('a', 'b', 3)")

    def test_equality_requires_same_orientation(self):
        # The data structure is undirected by convention, but the record
        # itself compares field-for-field.  Documenting that here keeps the
        # behaviour honest rather than surprising.
        self.assertEqual(Edge("a", "b", 3), Edge("a", "b", 3))
        self.assertNotEqual(Edge("a", "b", 3), Edge("b", "a", 3))
        self.assertNotEqual(Edge("a", "b", 3), Edge("a", "b", 4))

    def test_edges_are_hashable(self):
        edge = Edge("a", "b", 3)
        self.assertEqual({edge, Edge("a", "b", 3)}, {edge})

    def test_edge_is_not_equal_to_unrelated_object(self):
        self.assertNotEqual(Edge("a", "b", 3), "not an edge")


class DisjointSetTests(unittest.TestCase):
    def test_find_creates_singleton_for_unknown_element(self):
        ds = DisjointSet()
        self.assertEqual(ds.find("x"), "x")
        self.assertEqual(ds.num_sets(), 1)

    def test_union_reports_whether_a_merge_happened(self):
        ds = DisjointSet(["a", "b", "c"])
        self.assertTrue(ds.union("a", "b"))
        self.assertFalse(ds.union("a", "b"))
        self.assertTrue(ds.connected("a", "b"))
        self.assertFalse(ds.connected("a", "c"))
        self.assertEqual(ds.num_sets(), 2)

    def test_union_is_transitive(self):
        ds = DisjointSet(["a", "b", "c", "d"])
        ds.union("a", "b")
        ds.union("c", "d")
        ds.union("b", "c")
        self.assertTrue(ds.connected("a", "d"))
        self.assertEqual(ds.num_sets(), 1)

    def test_constructor_accepts_an_iterable(self):
        ds = DisjointSet(iter(["a", "b"]))
        self.assertEqual(ds.num_sets(), 2)

    def test_path_compression_keeps_representative_stable(self):
        ds = DisjointSet(range(50))
        for i in range(49):
            ds.union(i, i + 1)
        root = ds.find(0)
        self.assertEqual(ds.find(49), root)
        self.assertEqual(ds.num_sets(), 1)


class KruskalTests(unittest.TestCase):
    def test_empty_input_yields_empty_forest(self):
        self.assertEqual(kruskal_mst([]), [])

    def test_single_edge_is_the_tree(self):
        edge = Edge("a", "b", 7)
        self.assertEqual(kruskal_mst([edge]), [edge])

    def test_classic_triangle_picks_two_cheapest_edges(self):
        edges = [Edge("a", "b", 1), Edge("b", "c", 2), Edge("a", "c", 3)]
        result = kruskal_mst(edges)
        self.assertEqual(len(result), 2)
        self.assertEqual(total_weight(result), 3)
        self.assertNotIn(Edge("a", "c", 3), result)

    def test_disconnected_graph_yields_spanning_forest(self):
        edges = [
            Edge("a", "b", 1),
            Edge("b", "c", 2),
            Edge("x", "y", 5),
        ]
        result = kruskal_mst(edges)
        self.assertEqual(len(result), 3)
        self.assertEqual(total_weight(result), 8)

    def test_self_loops_are_dropped(self):
        edges = [Edge("a", "a", 1), Edge("a", "b", 2)]
        result = kruskal_mst(edges)
        self.assertEqual(result, [Edge("a", "b", 2)])

    def test_parallel_edges_keep_only_the_lighter(self):
        edges = [Edge("a", "b", 5), Edge("a", "b", 2)]
        result = kruskal_mst(edges)
        self.assertEqual(result, [Edge("a", "b", 2)])

    def test_parallel_edges_with_equal_weight_keep_one(self):
        edges = [Edge("a", "b", 2), Edge("a", "b", 2)]
        result = kruskal_mst(edges)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].weight, 2)

    def test_ties_preserve_input_order(self):
        first = Edge("a", "b", 1)
        second = Edge("b", "c", 1)
        third = Edge("a", "c", 1)
        result = kruskal_mst([first, second, third])
        self.assertEqual(result, [first, second])

    def test_input_iterable_is_not_mutated(self):
        edges = [Edge("a", "b", 1), Edge("b", "c", 2)]
        snapshot = list(edges)
        kruskal_mst(edges)
        self.assertEqual(edges, snapshot)

    def test_integer_vertices_and_negative_weights(self):
        edges = [
            Edge(0, 1, -3),
            Edge(1, 2, -1),
            Edge(0, 2, 4),
        ]
        result = kruskal_mst(edges)
        self.assertEqual(total_weight(result), -4)

    def test_float_weights_compared_with_tolerance(self):
        edges = [Edge("a", "b", 0.5), Edge("b", "c", 0.25)]
        result = kruskal_mst(edges)
        self.assertAlmostEqual(total_weight(result), 0.75, places=12)

    def test_vertex_appearing_only_in_one_edge_is_kept(self):
        # 'z' is an isolated vertex in the sense that it has no edges; it
        # simply never enters the disjoint set, so no stray entry appears.
        edges = [Edge("a", "b", 1)]
        result = kruskal_mst(edges)
        self.assertEqual(result, [Edge("a", "b", 1)])

    def test_repeated_calls_are_stable(self):
        edges = [Edge("a", "b", 2), Edge("b", "c", 1), Edge("a", "c", 3)]
        self.assertEqual(kruskal_mst(edges), kruskal_mst(edges))


class TotalWeightTests(unittest.TestCase):
    def test_empty_iterable_sums_to_integer_zero(self):
        self.assertEqual(total_weight([]), 0)
        self.assertIsInstance(total_weight([]), int)

    def test_integer_weights_stay_integral(self):
        self.assertEqual(total_weight([Edge("a", "b", 2), Edge("b", "c", 3)]), 5)
        self.assertIsInstance(total_weight([Edge("a", "b", 2)]), int)

    def test_mixed_weights_promote_to_float(self):
        self.assertAlmostEqual(
            total_weight([Edge("a", "b", 1), Edge("b", "c", 0.5)]), 1.5, places=12
        )


if __name__ == "__main__":
    unittest.main()
