"""Tikhonov-regularised inversion.

    x_est = (W^T W + alpha * G^T G)^-1 W^T dy

G is the anisotropic 3D discrete difference operator over the voxel grid, so
G^T G is the (weighted) grid Laplacian. The inverse problem is ill-posed because
link density is sparse relative to the voxel grid (L << M); the smoothness prior
pins it down.
"""

import numpy as np


def _indexer(shape):
    nx, ny, nz = shape

    def idx(i, j, k):
        return (i * ny + j) * nz + k

    return idx


def difference_operator(shape, weights=(1.0, 1.0, 1.0)):
    """Anisotropic first-difference operator G, shape (K, M).

    Kept explicit for small grids and for verifying `difference_laplacian`.
    """
    nx, ny, nz = shape
    idx = _indexer(shape)
    rows = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                u = idx(i, j, k)
                for w, (di, dj, dk) in zip(weights, ((1, 0, 0), (0, 1, 0), (0, 0, 1))):
                    ii, jj, kk = i + di, j + dj, k + dk
                    if ii < nx and jj < ny and kk < nz:
                        row = np.zeros(nx * ny * nz)
                        row[u] = -w
                        row[idx(ii, jj, kk)] = w
                        rows.append(row)
    M = nx * ny * nz
    return np.array(rows) if rows else np.zeros((0, M))


def difference_laplacian(shape, weights=(1.0, 1.0, 1.0)):
    """G^T G directly as an M x M matrix, without materialising G."""
    nx, ny, nz = shape
    idx = _indexer(shape)
    M = nx * ny * nz
    L = np.zeros((M, M))
    w2 = [w * w for w in weights]
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                u = idx(i, j, k)
                for a, (di, dj, dk) in enumerate(((1, 0, 0), (0, 1, 0), (0, 0, 1))):
                    ii, jj, kk = i + di, j + dj, k + dk
                    if ii < nx and jj < ny and kk < nz:
                        v = idx(ii, jj, kk)
                        L[u, u] += w2[a]
                        L[v, v] += w2[a]
                        L[u, v] -= w2[a]
                        L[v, u] -= w2[a]
    return L


def tikhonov(W, dy, alpha, GtG):
    """Solve for the regularised spatial loss field x_est."""
    M = W.shape[1]
    A = W.T @ W + alpha * GtG
    b = W.T @ dy
    return np.linalg.solve(A + 1e-12 * np.eye(M), b)


def recover_centroid(x, voxels):
    """Intensity-weighted centroid of a loss field — the tracked position."""
    w = np.clip(x, 0.0, None)
    s = float(w.sum())
    if s <= 0.0:
        return None
    return (voxels * w[:, None]).sum(axis=0) / s
