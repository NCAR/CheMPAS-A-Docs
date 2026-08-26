# LNOx Integration Summary

This note describes CheMPAS-A's lightning-NOx (LNOx) source scheme as
it currently stands in `src/core_atmosphere/chemistry/mpas_lightning_nox.F`.
It supersedes the historical `LNOx.md` note at the repository root,
which is preserved there as the original DC3 motivation record.

The current source and namelist contract, rather than the archived development
design, are authoritative for the isotherm-mode implementation.

## Scope

The LNOx scheme is an operator-split source term that injects NO into
prognostic tracer cells in active convection, ahead of the MICM solver
call within each chemistry timestep. It is independent of the MICM
mechanism YAML and of the TUV-x photolysis configuration: any MICM
mechanism that carries a `qNO` species will receive the source.

Two gating modes are available:

- **Altitude mode** (default, inherited from DAVINCI-MPAS) — emission
  in a fixed altitude window, with rate scaled linearly by updraft
  excess.
- **Isotherm mode** (new, faithful to the LNOx.md DC3 framing) —
  emission in a temperature window matching the mixed-phase layer,
  with constant rate.

Both modes additionally require updraft `w` to exceed
`config_lnox_w_threshold`; outside active convection, no NO is injected.

## Gating modes

| Mode | Gate | Rate |
|---|---|---|
| `altitude` (default) | `z_min ≤ z ≤ z_max` AND `w > w_threshold` | `S = source_rate · (w − w_threshold) / w_ref` |
| `isotherm` (new) | `t_min ≤ T ≤ t_max` AND `w > w_threshold` | `S = source_rate` (constant) |

The 233.15–262.15 K isotherm window is the canonical mixed-phase layer
where charge separation drives lightning in deep convection. The 1 ppbv
NOx target at cloud top, and the constant emission framing, come from
the DC3 supercell parcel-model description preserved in `LNOx.md` at
the repository root.

Altitude mode is retained for backward compatibility with existing
runs and for cases where the user wants to specify a literal injection
volume independent of the storm thermal structure.

Both gating modes follow the original DC3 parcel-model design in
`LNOx.md`: they apply a mixing-ratio rate to parcels in an idealized
storm, not a flash-rate or molecule-count source. In altitude mode,
`z_min` and `z_max` are applied to MPAS `zgrid` height above MSL, not
AGL, so over terrain the injection layer does not follow the surface.
Because `config_lnox_source_rate` is a mixing-ratio rate in ppbv s⁻¹,
the total injected moles scale with each cell's air mass; integrated
production is therefore resolution-dependent on variable meshes. These
assumptions are appropriate for flat-terrain idealized cases only and
should be recalibrated before using LNOx in terrain-following or
variable-resolution applications.

## Namelist options

LNOx source options are members of the `&lnox` namelist group. The
fallback photolysis option `config_j_no2_max` is in `&photolysis`.
Defaults shown match `src/core_atmosphere/Registry.xml`.

| Option | Type | Default | Used in | Description |
|---|---|---|---|---|
| `config_lnox_gating_mode` | character | `'altitude'` | both | Selects the gate; `'altitude'` or `'isotherm'`. An unknown value produces an `MPAS_LOG_CRIT` message and aborts initialization. |
| `config_lnox_source_rate` | real | `0.0` | both | Source mixing-ratio rate amplitude; ppbv s⁻¹. Zero disables the source. Altitude mode multiplies by `(w − w_threshold) / w_ref`; isotherm mode applies it as a constant. Total injected moles scale with cell air mass. |
| `config_lnox_w_threshold` | real | `5.0` | both | Updraft threshold (m s⁻¹) below which no NO is injected. |
| `config_lnox_w_ref` | real | `10.0` | both (formula: altitude only) | Reference updraft (m s⁻¹) for the altitude-mode rate normalization. The isotherm formula does not use it, but the current initializer still requires it to be positive; a nonpositive value disables either mode. |
| `config_lnox_z_min` | real | `5000.0` | altitude only | Lower altitude bound (m above MSL from `zgrid`, not AGL). Ignored in isotherm mode. |
| `config_lnox_z_max` | real | `12000.0` | altitude only | Upper altitude bound (m above MSL from `zgrid`, not AGL). Ignored in isotherm mode. |
| `config_lnox_t_min` | real | `233.15` | isotherm only | Cold isotherm bound (K). Ignored in altitude mode. |
| `config_lnox_t_max` | real | `262.15` | isotherm only | Warm isotherm bound (K). Ignored in altitude mode. |
| `config_j_no2_max` | real | `0.0` | both | Daytime peak `jNO2` for the fallback solar-geometry photolysis path; not part of the LNOx source itself and configured in `&photolysis`. |
| `config_lnox_nox_tau` | real | `0.0` | both | Optional NOx relaxation timescale (s); zero disables. |

## Code paths

The implementation lives in two files. Routine names are used instead of
volatile source-line references:

- `src/core_atmosphere/chemistry/mpas_lightning_nox.F`
  - `lightning_nox_init` — parses `config_lnox_gating_mode`,
    sets the module-level integer `mode = MODE_ALTITUDE | MODE_ISOTHERM`,
    reads dimensions/configuration from the supplied MPAS pools, validates the
    common and mode-specific inputs, and logs the resolved configuration.
  - `lightning_nox_inject` — operates on plain Fortran arrays and branches on
    `mode` for the per-cell loop.
    Accepts an optional `temperature(:,:)` argument; in isotherm mode
    the absence of the argument is treated as a no-op.
- `src/core_atmosphere/chemistry/mpas_atm_chemistry.F`
  - The inject call site passes the reconstructed chemistry environment
    temperature, `T = theta_m / (1 + rvord·qv) · exner`, for isotherm
    gating. Altitude mode ignores that optional argument.

`lightning_nox_init` accesses the supplied MPAS dimension, configuration, and
state pools to resolve its settings and `index_qNO`. The injection kernel
itself is pool-independent and receives plain arrays;
`mpas_atm_chemistry.F` reconstructs and supplies temperature from `theta_m`,
`exner`, and `qv` for isotherm gating.

## Calibration notes

The LNOx.md DC3 description targets ~1 ppbv NOx at cloud top in a
supercell with ~5 m s⁻¹ sustained updrafts. For isotherm mode, a
starting point that gives an order-of-magnitude-correct first run is

```
config_lnox_source_rate = 1.0e-3   ! ppbv/s
```

(reasoning: an air parcel takes ~1000 s to traverse the 262–233 K
mixed-phase layer in a strong updraft; 1.0e-3 ppbv/s × 1000 s ≈ 1 ppbv).

Refinement is a manual retune-and-rerun loop: inspect peak NOx in the convective
core, adjust `config_lnox_source_rate` by a small factor, and re-run. The
tracked `scripts/plot_lnox_o3.py` is not currently a usable path: its custom
colormap construction fails before argument parsing (including `--help`). Use
NetCDF/xarray or another verified viewer for `qNO`, `qNO2`, and `qO3` until the
plotter is corrected.

For altitude mode, the DAVINCI-era working value `source_rate = 0.5`
(paired with the Registry defaults `w_threshold = 5.0`, `w_ref = 10.0`)
produces a visually similar enhancement on the supercell case;
calibration there is also a manual loop.

The repository regression infrastructure is present and the accepted MVP
matrix records 268 Python tests plus 16 shell contracts passing. It does not
yet publish a dedicated numerical reference for both LNOx gating modes, so
retain the manual calibration check above and compare against the recorded
[runtime evidence](../results/TEST_RUNS.md) when changing this source.

## See also

- [Public idealized examples](https://github.com/NCAR/CheMPAS-A/wiki/Idealized-Test-Cases) — the released supercell lightning-NOx configuration
- [Chapter 2](../../tutorial/02-deep-convection.md) — worked examples for both modes
- [MUSICA/MICM coupling](../musica/MUSICA_INTEGRATION.md)
- [TUV-x photolysis](TUVX_INTEGRATION.md) — including the `config_j_no2_max` fallback path
