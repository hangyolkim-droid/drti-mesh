import unittest

import numpy as np

from drti.fresnel import sensitivity_matrix, wavelength
from drti.geometry import link_count, links, six_node_room
from drti.inversion import difference_laplacian, difference_operator, recover_centroid, tikhonov
from drti.scanrate import DEFAULT_LINK_TIME_S, sample_spacing, scan_hz, table
from drti.simulate import blob, run_demo


class GeometryTests(unittest.TestCase):
    def test_link_count(self):
        self.assertEqual(link_count(4), 6)
        self.assertEqual(link_count(6), 15)
        self.assertEqual(link_count(8), 28)
        self.assertEqual(link_count(10), 45)
        self.assertEqual(link_count(90), 4005)

    def test_six_node_room_links(self):
        self.assertEqual(len(links(six_node_room())), 15)

    def test_ring_nodes(self):
        from drti.geometry import ring_nodes
        self.assertEqual(len(ring_nodes(3.5, 3.5, 8)), 8)
        self.assertEqual(len(links(ring_nodes(3.5, 3.5, 8))), 28)


class FresnelTests(unittest.TestCase):
    def test_fresnel_zone_mask_and_weight(self):
        nodes = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        voxels = np.array([[0.5, 0.0, 0.0], [0.5, 10.0, 0.0]])
        W, edges = sensitivity_matrix(nodes, voxels, wavelength(2.4e9))
        self.assertEqual(W.shape, (1, 2))
        self.assertAlmostEqual(W[0, 0], 1.0, places=6)   # D = 1 m -> 1/sqrt(D)
        self.assertEqual(W[0, 1], 0.0)                   # outside the Fresnel zone

    def test_wavelength(self):
        self.assertAlmostEqual(wavelength(2.4e9), 0.1249135, places=6)


class InversionTests(unittest.TestCase):
    def test_laplacian_is_gtg(self):
        shape = (3, 2, 2)
        G = difference_operator(shape)
        self.assertTrue(np.allclose(G.T @ G, difference_laplacian(shape)))

    def test_recover_centroid(self):
        voxels = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        self.assertAlmostEqual(recover_centroid(np.array([0.0, 2.0]), voxels)[0], 1.0)

    def test_tikhonov_shapes(self):
        W = np.eye(3)
        shape = (3, 1, 1)
        x = tikhonov(W, np.array([1.0, 2.0, 3.0]), 1e-3, difference_laplacian(shape))
        self.assertEqual(x.shape, (3,))


class ScanRateTests(unittest.TestCase):
    def test_scan_rate_matches_baseline_table(self):
        hz = {n: hz for n, _, hz in table((4, 6, 8, 10))}
        self.assertEqual(round(hz[4], 1), 16.7)
        self.assertEqual(round(hz[6], 1), 6.7)
        self.assertEqual(round(hz[8], 1), 3.6)
        self.assertEqual(round(hz[10], 1), 2.2)

    def test_spacing(self):
        self.assertAlmostEqual(sample_spacing(1.4, 7.0), 0.2, places=6)


class SimulationTests(unittest.TestCase):
    def test_blob_peak(self):
        voxels = np.array([[0.0, 0.0, 0.0]])
        self.assertAlmostEqual(float(blob(voxels, [0, 0, 0], 0.5)[0]), 1.0)

    def test_demo_recovers_centroid(self):
        r = run_demo(res=0.5, alpha=1e-2, noise_std=0.0, seed=0)
        self.assertEqual(r["links"], 15)
        self.assertLess(r["centroid_error_m"], 0.5)

    def test_demo_is_deterministic(self):
        a = run_demo(seed=1)
        b = run_demo(seed=1)
        self.assertEqual(a["field_rmse"], b["field_rmse"])


if __name__ == "__main__":
    unittest.main()
