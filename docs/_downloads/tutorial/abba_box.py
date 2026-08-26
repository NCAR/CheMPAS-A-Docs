#!/usr/bin/env python3
"""Standalone MUSICA-Python box model for the ABBA toy mechanism.

Mirrors section 2.5 of the CheMPAS-A tutorial (the supercell + ABBA
run) without MPAS in the loop. Single grid cell, slow two-way reaction
qAB <-> qA + qB, 2 h integration. Output: abba_box.nc, abba_box.png
(300 dpi), abba_box.pdf.

Run:
    ~/miniconda3/envs/mpas/bin/python scripts/musica_python/abba_box.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# scripts/style.py lives one level up.
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

import musica
from musica.constants import GAS_CONSTANT
from musica.mechanism_configuration import Parser
from musica.micm.solver_result import SolverState

import style

REPO_ROOT = Path(__file__).parent.parent.parent
ABBA_YAML = REPO_ROOT / "micm_configs" / "abba.yaml"
OUT_DIR = Path(__file__).parent

# Reference conditions for the box.
T_REF = 273.0     # K
P_REF = 101325.0  # Pa

# Initial AB mixing ratio (ppm). A and B start at zero; AB dissociates
# toward equilibrium. Chosen so all species sit near ~1 ppm.
AB_INIT_PPM = 1.0


def main() -> None:
    style.apply_ncar_style()

    parser = Parser()
    mechanism = parser.parse(str(ABBA_YAML))
    solver = musica.MICM(
        mechanism=mechanism,
        solver_type=musica.SolverType.rosenbrock_standard_order,
    )
    state = solver.create_state(number_of_grid_cells=1)
    state.set_conditions(temperatures=T_REF, pressures=P_REF)

    # mol/m^3 <-> ppm via VMR = n*R*T/P; ppm = VMR * 1e6.
    to_ppm = GAS_CONSTANT * T_REF / P_REF * 1e6
    ab_init = AB_INIT_PPM / to_ppm   # mol m^-3
    state.set_concentrations({"A": [0.0], "B": [0.0], "AB": [ab_init]})

    # USER_DEFINED rate parameters are *multipliers* on the YAML
    # scaling_factor; effective k = USER * scaling_factor. The forward
    # reaction AB -> A + B is first order, so its multiplier stays 1.0
    # (k_fwd = 2e-3 s^-1, as in the MPAS-coupled §2.5 run).
    #
    # The reverse A + B -> AB is *second order* (k_rev has units
    # m^3 mol^-1 s^-1), so its rate falls as concentration^2. To hold the
    # equilibrium fractions fixed (AB ~ 0.268, A = B ~ 0.732 of total)
    # while running at ~1 ppm instead of ~1 mol m^-3, k_rev must scale up
    # by the same factor the concentration dropped: to_ppm / AB_INIT_PPM.
    # This keeps K = k_fwd / k_rev proportional to total mass, which is
    # what makes the fractional partitioning concentration-independent.
    rev_mult = to_ppm / AB_INIT_PPM
    user = state.get_user_defined_rate_parameters()
    user["USER.forward_AB_to_A_B"] = [1.0]
    user["USER.reverse_A_B_to_AB"] = [rev_mult]
    state.set_user_defined_rate_parameters(user)

    dt_out = 60.0       # output cadence (s)
    t_end  = 7200.0     # 2 h
    times = [0.0]
    history = [{k: float(v[0]) for k, v in state.get_concentrations().items()}]

    while times[-1] < t_end:
        elapsed = 0.0
        while elapsed < dt_out:
            r = solver.solve(state, dt_out - elapsed)
            elapsed += r.stats.final_time
            if r.state != SolverState.Converged:
                print(f"  solver state: {r.state} at t={times[-1] + elapsed:.1f}")
        times.append(times[-1] + dt_out)
        history.append({k: float(v[0]) for k, v in state.get_concentrations().items()})

    minutes = np.array(times) / 60.0
    ds = xr.Dataset(
        {sp: ("time", np.array([h[sp] for h in history])) for sp in ("A", "B", "AB")},
        coords={"time": minutes},
        attrs={"mechanism": "abba.yaml", "T_K": T_REF, "P_Pa": P_REF},
    )
    ds["time"].attrs["units"] = "minutes"
    for sp in ("A", "B", "AB"):
        ds[sp].attrs["units"] = "mol m-3"
    ds.to_netcdf(OUT_DIR / "abba_box.nc", engine="scipy")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    palette = style.get_palette(2)
    # A and B coincide exactly (A = B by symmetry), so plot AB and A
    # only; label A to show it stands for both curves.
    series = (
        ("AB", style.species_label("AB")),
        ("A", f"{style.species_label('A')} = {style.species_label('B')}"),
    )
    for (sp, label), color in zip(series, palette):
        ax.plot(minutes, ds[sp].values * to_ppm, color=color, label=label)
    ax.set_xlabel("Time [min]")
    ax.set_ylabel("Mixing ratio [ppm]")
    ax.set_title(style.format_title("ABBA box model"))
    ax.legend()
    ax.grid(True, alpha=0.4)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "abba_box.png", dpi=300)
    fig.savefig(OUT_DIR / "abba_box.pdf")
    print(
        f"Wrote {OUT_DIR / 'abba_box.nc'}, {OUT_DIR / 'abba_box.png'}, "
        f"and {OUT_DIR / 'abba_box.pdf'}."
    )


if __name__ == "__main__":
    main()
