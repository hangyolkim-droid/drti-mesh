"""Command-line entry points for the D-RTI baseline."""

import argparse

import numpy as np

from . import __version__
from .geometry import link_count, ring_nodes
from .scanrate import sample_spacing, scan_hz, table
from .simulate import run_demo


def build_parser():
    p = argparse.ArgumentParser(prog="drti", description="D-RTI baseline (simulation only)")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("mesh", help="link count and scan rate for N nodes")
    sp.add_argument("--nodes", type=int, default=6)

    sub.add_parser("scan", help="scan-rate table vs node count")

    sp = sub.add_parser("sweep", help="localization error vs node count (resolution/scan-rate trade-off)")
    sp.add_argument("--res", type=float, default=0.5)
    sp.add_argument("--alpha", type=float, default=1e-2)
    sp.add_argument("--noise-std", type=float, default=0.0)
    sp.add_argument("--trials", type=int, default=20, help="random target positions per node count")
    sp.add_argument("--seed", type=int, default=0)

    sp = sub.add_parser("sim", help="synthetic forward model + Tikhonov inversion")
    sp.add_argument("--res", type=float, default=0.5, help="voxel resolution (m)")
    sp.add_argument("--alpha", type=float, default=1e-2, help="Tikhonov alpha")
    sp.add_argument("--noise-std", type=float, default=0.0, help="link noise std")
    sp.add_argument("--freq-hz", type=float, default=2.4e9)
    sp.add_argument("--seed", type=int, default=0)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.cmd == "mesh":
        n = args.nodes
        print(f"nodes={n}  links={link_count(n)}  scan={scan_hz(n):.2f} Hz"
              f"  (~{sample_spacing(1.4, scan_hz(n)) * 100:.0f} cm between samples @1.4 m/s)")
        return 0

    if args.cmd == "scan":
        print(f"{'nodes':>5} {'links':>6} {'scan Hz':>8} {'spacing (cm)':>13}")
        for n, l, hz in table():
            print(f"{n:>5} {l:>6} {hz:>8.2f} {sample_spacing(1.4, hz) * 100:>13.0f}")
        return 0

    if args.cmd == "sweep":
        rng = np.random.default_rng(args.seed)
        print(f"{args.trials} random targets per node count, res={args.res} m")
        print(f"{'nodes':>5} {'links':>6} {'scan Hz':>8} {'mean err (cm)':>14} {'sd':>6}")
        for n in (4, 6, 8, 10):
            nodes = ring_nodes(3.5, 3.5, n)
            errs = []
            for _ in range(args.trials):
                tgt = [rng.uniform(0.3, 3.2), rng.uniform(0.3, 3.2), rng.uniform(0.4, 2.0)]
                r = run_demo(res=args.res, alpha=args.alpha, noise_std=args.noise_std,
                             nodes=nodes, target=tgt)
                errs.append(r["centroid_error_m"])
            errs = np.array(errs)
            print(f"{n:>5} {link_count(n):>6} {scan_hz(n):>8.2f} "
                  f"{errs.mean() * 100:>14.1f} {errs.std() * 100:>6.1f}")
        return 0

    if args.cmd == "sim":
        r = run_demo(res=args.res, alpha=args.alpha, noise_std=args.noise_std,
                     freq_hz=args.freq_hz, seed=args.seed)
        print(f"nodes={r['nodes']}  links={r['links']}  voxels={r['voxels']}  "
              f"grid={r['shape']}  lambda={r['wavelength_m'] * 100:.1f} cm")
        print(f"true target : {np.round(r['target_true_m'], 3)} m")
        print(f"estimated   : {np.round(r['target_est_m'], 3)} m")
        print(f"centroid err: {r['centroid_error_m'] * 100:.1f} cm   "
              f"field RMSE: {r['field_rmse']:.5f}")
        return 0

    return 2
