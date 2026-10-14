"""Node layouts, link enumeration, and voxel grids."""

import itertools

import numpy as np


def link_count(n):
    """Links in a full mesh of n nodes: L = n(n-1)/2."""
    return n * (n - 1) // 2


def links(nodes):
    """All unordered TX/RX pairs as (i, j) index tuples."""
    return list(itertools.combinations(range(len(nodes)), 2))


def corners(width, depth, heights):
    """Four corner nodes at the given heights."""
    return np.array([[0.0, 0.0, heights[0]],
                     [width, 0.0, heights[1]],
                     [width, depth, heights[2]],
                     [0.0, depth, heights[3]]])


def mid_wall(width, depth, heights=(2.1, 0.9)):
    """Two mid-wall nodes (above the door, below the window)."""
    return np.array([[width / 2.0, 0.0, heights[0]],
                     [width / 2.0, depth, heights[1]]])


def six_node_room(width=3.5, depth=3.5):
    """The baseline geometry: 4 corners at staggered heights + 2 mid-wall.

    Staggering heights (1.8 / 1.8 / 0.9 / 0.9 m) gives coarse z-discrimination
    without extra nodes or corner-diagonal ambiguity.
    """
    return np.vstack([corners(width, depth, (1.8, 1.8, 0.9, 0.9)),
                      mid_wall(width, depth)])


def ring_nodes(width, depth, n, z_lo=0.9, z_hi=1.8):
    """N nodes spaced evenly around the room perimeter, heights alternating.

    A generic layout for sweeping node count; for the baseline geometry see
    `six_node_room`.
    """
    per = 2.0 * (width + depth)
    pts = []
    for k in range(n):
        s = (per * k / n) % per
        if s < width:
            x, y = s, 0.0
        elif s < width + depth:
            x, y = width, s - width
        elif s < 2.0 * width + depth:
            x, y = width - (s - width - depth), depth
        else:
            x, y = 0.0, depth - (s - 2.0 * width - depth)
        pts.append([x, y, z_hi if k % 2 == 0 else z_lo])
    return np.array(pts)


def voxel_grid(width, depth, height, res):
    """Centres of an M-voxel grid.

    Returns (voxels, shape) where voxels is (M, 3) and shape is (nx, ny, nz).
    """
    xs = np.arange(res / 2.0, width, res)
    ys = np.arange(res / 2.0, depth, res)
    zs = np.arange(res / 2.0, height, res)
    grid = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), axis=-1)
    return grid.reshape(-1, 3), (len(xs), len(ys), len(zs))
