"""Synthetic forward model + reconstruction demo.

This is a *simulation*: a known spatial loss field is pushed through the Fresnel
sensitivity matrix to produce synthetic link attenuations, then recovered by
Tikhonov inversion and reduced to a tracked centroid. Nothing here is a hardware
measurement.
"""

import numpy as np

from .fresnel import sensitivity_matrix, wavelength
from .geometry import six_node_room, voxel_grid
from .inversion import difference_laplacian, recover_centroid, tikhonov


def blob(voxels, center, sigma, magnitude=1.0):
    """Isotropic Gaussian loss blob — a stand-in for one occupant."""
    d2 = ((voxels - np.asarray(center, dtype=float)) ** 2).sum(axis=1)
    return magnitude * np.exp(-d2 / (2.0 * sigma ** 2))


def run_demo(width=3.5, depth=3.5, height=2.4, res=0.5, freq_hz=2.4e9,
             alpha=1e-2, noise_std=0.0, seed=0, target=None, sigma=0.4, nodes=None):
    rng = np.random.default_rng(seed)
    if nodes is None:
        nodes = six_node_room(width, depth)
    voxels, shape = voxel_grid(width, depth, height, res)
    wl = wavelength(freq_hz)

    W, edges = sensitivity_matrix(nodes, voxels, wl)
    if target is None:
        target = np.array([width * 0.35, depth * 0.60, 1.0])
    x_true = blob(voxels, target, sigma)

    dy = W @ x_true
    if noise_std > 0.0:
        dy = dy + rng.normal(0.0, noise_std, size=dy.shape)

    x_est = tikhonov(W, dy, alpha, difference_laplacian(shape))

    c_true = recover_centroid(x_true, voxels)
    c_est = recover_centroid(x_est, voxels)
    err = float(np.linalg.norm(c_est - c_true)) if c_est is not None else float("nan")

    return {
        "nodes": len(nodes),
        "links": len(edges),
        "voxels": len(voxels),
        "shape": tuple(int(s) for s in shape),
        "wavelength_m": wl,
        "alpha": alpha,
        "noise_std": noise_std,
        "target_true_m": [float(v) for v in c_true],
        "target_est_m": [float(v) for v in (c_est if c_est is not None else [])],
        "centroid_error_m": err,
        "field_rmse": float(np.sqrt(np.mean((x_est - x_true) ** 2))),
    }
