# D-RTI baseline

Companion documentation for the article
**“Distributed Radio Tomographic Imaging (D-RTI) on Commodity Edge Nodes.”**

**Status: mathematical baseline. Simulation only — no hardware instrumented, no RF measurements
taken.** Every number below comes from the synthetic forward model in `drti.simulate`.

---

## 1. Forward model

A mesh of `N` nodes produces `L = N(N-1)/2` links. Human motion perturbs the local complex
permittivity along those links, attenuating them:

    dy = W x + n

- `dy` — L×1 vector of measured link-attenuation deltas
- `x`  — M×1 spatial voxel loss field
- `n`  — L×1 measurement noise
- `W`  — L×M sensitivity matrix

## 2. Fresnel sensitivity matrix

Following the cylindrical-wave approximation (Wilson & Patwari, 2010), for link `l` between
transmitter `t_l` and receiver `r_l`, with `D_l = ||t_l − r_l||`:

    W_lj = 1 / sqrt(D_l)   if d_l1(p_j) + d_l2(p_j) < D_l + lambda/2
    W_lj = 0               otherwise

where `d_l1(p) = ||p − t_l||` and `d_l2(p) = ||p − r_l||`. Only voxels inside the first Fresnel
ellipsoid contribute, so `W` is sparse by construction (kept dense here for clarity).

Implemented in `drti/fresnel.py`.

## 3. Inversion

Link density is sparse relative to the voxel grid (`L << M`) and the problem is ill-posed.
Spatial smoothness is enforced with an anisotropic 3D discrete difference operator `G`:

    x_est = (W^T W + alpha * G^T G)^-1 W^T dy

`G^T G` is the weighted grid Laplacian, built directly in `drti/inversion.py`
(`difference_laplacian`) to avoid materialising `G`. The ridge parameter `alpha` trades fit
against smoothness; it should be tuned against an empirical link-variance covariance from an
empty-room calibration pass (see the article's Engineering Realities).

Tracked position = intensity-weighted centroid of `x_est`.

## 4. Scan-rate bound

On unrooted commodity phones the OS sandbox blocks monitor-mode capture, so links are probed as
sequential pairwise unicast on a half-duplex channel:

    scan_hz = 1 / (L * link_time)

`link_time` is an **assumption** (default 10 ms/link). It reproduces the baseline table:

| nodes | links | scan Hz |
|---|---|---|
| 4 | 6 | 16.7 |
| 6 | 15 | 6.7 |
| 8 | 28 | 3.6 |
| 10 | 45 | 2.2 |

At a 1.4 m/s walk this is 8 cm to 63 cm of movement between scans.

## 5. Baseline geometry

`drti.geometry.six_node_room`: four corners at staggered heights (1.8, 1.8, 0.9, 0.9 m) plus two
mid-wall nodes (above the door, below the window). Fifteen links, no corner-diagonal ambiguity,
coarse z-discrimination from the stagger alone.

## 6. Baseline result

`drti sweep --trials 20 --res 0.5` — 20 random targets per node count, 3.5 × 3.5 m room, α = 1e-2,
no link noise:

| nodes | links | scan Hz | mean centroid error | sd |
|---|---|---|---|---|
| 4 | 6 | 16.7 | 77.4 cm | 22.6 |
| 6 | 15 | 6.7 | 48.6 cm | 20.9 |
| 8 | 28 | 3.6 | 28.5 cm | 13.9 |
| 10 | 45 | 2.2 | 22.5 cm | 12.2 |

**Interpretation.** Localization improves monotonically with node count while scan rate degrades
just as monotonically — the central trade-off of the article. The 6-node row (~0.5 m mean centroid
error) is consistent with the article's stated 0.6–0.8 m expectation for that geometry.

These are *simulation* error magnitudes. They are not a hardware accuracy claim.

## 7. Assumptions & known limitations

- Geometric Fresnel weights only: no multipath, no wall-material loss, no antenna pattern.
- `link_time` uncharacterised on real devices; scan rates are model-derived.
- Dense linear algebra — fine to ~2000 voxels here; production needs sparse + matrix-free solving.
- Single Gaussian target; no multi-target or kinematic (EKF) stage implemented yet.
- Synchronisation, acoustic band-limiting, and speaker non-linearity are **not** modelled here;
  they belong to the (separate) acoustic/companion work.

## 8. Reproduce

```
pip install -e .
drti scan
drti sweep --trials 20 --res 0.5
python -m unittest discover -s tests
```
