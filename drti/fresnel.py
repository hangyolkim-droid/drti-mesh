"""First Fresnel-zone sensitivity matrix.

Forward model:  dy = W x + n
Weight for voxel j on link l, following the cylindrical-wave approximation in
Wilson & Patwari, "Radio Tomographic Imaging with Wireless Networks"
(IEEE Trans. Mobile Computing, 2010):

    W_lj = 1 / sqrt(D_l)   if d_l1(p_j) + d_l2(p_j) < D_l + lambda/2
    W_lj = 0               otherwise

where D_l = ||t_l - r_l||, d_l1(p) = ||p - t_l||, d_l2(p) = ||p - r_l||.
"""

import numpy as np

from .geometry import links

C_LIGHT = 299_792_458.0


def wavelength(freq_hz, c=C_LIGHT):
    """Free-space wavelength in metres."""
    return c / freq_hz


def sensitivity_matrix(nodes, voxels, wl):
    """Dense L x M Fresnel sensitivity matrix W.

    W is sparse by construction (only voxels inside the first Fresnel ellipsoid
    of each link are non-zero); this baseline keeps it dense for clarity.
    """
    edges = links(nodes)
    n_links, n_voxels = len(edges), len(voxels)
    W = np.zeros((n_links, n_voxels), dtype=float)

    for li, (i, j) in enumerate(edges):
        t, r = nodes[i], nodes[j]
        D = float(np.linalg.norm(t - r))
        d1 = np.linalg.norm(voxels - t, axis=1)
        d2 = np.linalg.norm(voxels - r, axis=1)
        inside = (d1 + d2) < (D + wl / 2.0)      # first Fresnel zone
        W[li, inside] = 1.0 / np.sqrt(D)

    return W, edges
