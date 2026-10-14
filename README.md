# drti-mesh

A **D-RTI baseline**: Fresnel-zone RF tomography on commodity edge nodes.

Reference implementation for the article
**“Four Phones, Six Links, One Underdetermined Inverse Problem: A D-RTI Concept.”**

> **Scope: simulation only.** No hardware has been instrumented and no RF
> measurements have been taken. Everything here is the *mathematical* baseline —
> no result in this repo has been validated against physical hardware.

## What's here

| Module | Contents |
|---|---|
| `drti.geometry` | node layouts (baseline 6-node room, N-node ring) and voxel grids |
| `drti.fresnel` | first Fresnel-zone sensitivity matrix `W` (Wilson & Patwari, 2010) |
| `drti.inversion` | Tikhonov-regularised inversion with an anisotropic 3D difference operator |
| `drti.simulate` | synthetic forward model + reconstruction demo |
| `drti.scanrate` | the scan-rate bound for sequential pairwise probing |
| `drti.cli` | command-line entry points |

## Install

```
pip install -e .
```

Needs Python 3.8+ and `numpy`.

## Use

```
drti scan                    # scan-rate table vs node count
drti mesh --nodes 6          # links + scan rate for N nodes
drti sim --res 0.5           # synthetic forward model + inversion
drti sweep --trials 20       # localization error vs node count
```

## Baseline result (simulation)

20 random target positions per node count · 3.5 × 3.5 m room · 0.5 m voxels ·
α = 1e-2 · no link noise:

| nodes | links | scan Hz | mean centroid error | sd |
|---|---|---|---|---|
| 4 | 6 | 16.7 | 77.4 cm | 22.6 |
| 6 | 15 | 6.7 | 48.6 cm | 20.9 |
| 8 | 28 | 3.6 | 28.5 cm | 13.9 |
| 10 | 45 | 2.2 | 22.5 cm | 12.2 |

The trade-off *is* the result: more nodes localize better and scan slower. The 6-node row
(~0.5 m mean centroid error) is consistent with the article's stated 0.6–0.8 m expectation.

## Caveats (read these)

- **Simulation only.** Synthetic link attenuations; no RF hardware in the loop.
- **`link_time` is an assumption, not a measurement.** The default 10 ms/link reproduces the
  baseline scan-rate table; it has not been characterised on real phones.
- **Dense linear algebra.** Fine for the small grids here (a few thousand voxels); production
  needs sparse operators and a matrix-free (e.g. conjugate-gradient) solver.
- **`W` is physics-idealised** — geometric Fresnel ellipsoids with a cylindrical-wave weight,
  no multipath, no wall-material loss model.

## Roadmap

- **v0.2 — multipath & baseline drift.** Model time-varying baseline drift, multipath variance, and
  rolling median filtering, then show centroid recovery under a drifting baseline.
  *(Today the repo does **not** model multipath. The Δy / rolling-baseline / median-filter
  mitigation is an architectural proposal, not a simulated feature.)*
- **Sparse / matrix-free solver.** Replace the dense normal-equation solve so voxel grids scale past
  a few thousand.
- **Multi-target + kinematic stage.** EKF hand-off from voxel probability blobs to position/velocity
  tracks.

## Production path

The route from this simulation baseline to a physical node mesh — broadcast probing, dropped-link
recovery, phase, TDMA sync, and interference — is written up in
[docs/production-path.md](docs/production-path.md).

## Prior art & what's new here

RTI with a Fresnel-zone forward model is Wilson & Patwari (2010), and commodity-equipment RTI has
been demonstrated before (see References). The contribution here is narrower: the *unrooted-phone*
constraint. The OS sandbox forces sequential pairwise unicast, which puts an `O(N^2)` airtime floor
under the sweep and makes scan rate — not resolution — the binding limit.

## References & prior art

- Wilson & Patwari, “Radio Tomographic Imaging with Wireless Networks” (IEEE Trans. Mobile
  Computing, 2010) — Fresnel-zone link sensitivity.
- *Democratized Radio Tomography: Using Consumer Equipment to See through Walls* (IEEE, 2019) —
  prior art for commodity-equipment RTI.
- *Through-the-Wall Imaging Exploiting 2.4 GHz Commodity Wi-Fi* (arXiv:1903.03895, 2019) —
  three-dimensional through-wall imaging on commodity hardware.
- Weerasiri, *Indoor Radio Tomographic Imaging with Sparse Device Topologies* (thesis, University
  of Colombo School of Computing) — CSI-based RTI on ESP-class nodes with a round-robin protocol.
- Karanam et al., “3D Through-Wall Imaging with Unmanned Aerial Vehicles Using WiFi”
  (IPSN 2017) — 3D RF tomography from mobile transceivers.
- Christensen et al., “BatVision: Learning to See 3D Spatial Layout with Two Ears”
  (ICRA 2020) — companion article's inspiration.

## License

MIT — see `LICENSE`.
