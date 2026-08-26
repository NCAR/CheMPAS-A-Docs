# Chapter 1: Overview

The CheMPAS-A Tutorial walks through CheMPAS-A's idealized chemistry test
cases. Where the [User's Guide](../users-guide/index.rst) is a reference-style
CheMPAS-A adaptation of the upstream MPAS-Atmosphere documentation, this
tutorial is narrative: run the case, look at the output, understand what the
chemistry is doing.

The tutorial cases are teaching and development examples. For the verified
global MVP, use the public reconstruction guide and evidence record linked
under [Beyond the tutorial](#beyond-the-tutorial) rather than treating an
idealized case as production forcing.

## What this tutorial assumes

- `atmosphere_model` is built. See the public MVP
  [build guide](https://github.com/NCAR/CheMPAS-A/wiki/Building) and
  [Chapter 3 of the User's Guide](../users-guide/03-building.md).
- A separate run-data root is set up with each case's namelist, streams,
  graph partition, and (where needed) initial-condition files. The examples
  call this location `$CHEMPAS_RUN_ROOT`; obtain the public inputs from the
  [examples wiki](https://github.com/NCAR/CheMPAS-A/wiki/Examples).
- The conda environment `mpas` is available for plotting:
  `conda activate mpas`.
- For coupled TUV-x runs, `CHEMPAS_TUVX_DATA` points to a MUSICA source
  checkout's `configs/tuvx/data` directory. Chapters 2--4 stage that tree as
  `data` in each run directory because the TUV-x JSON paths are relative.

## Python environment for standalone examples

The MPAS-coupled plotting examples use the base `mpas` conda environment
(`numpy`, `xarray`, `matplotlib`, `netCDF4`, and `scipy`); Chapter 4's global
maps also require `cartopy`. The standalone MUSICA-Python examples need
MUSICA's tutorial dependencies:

```bash
conda activate mpas
pip install 'musica[tutorial]' ephem
```

- `musica` — MUSICA-Python bindings: MICM solver, TUV-x calculator,
  mechanism-configuration parser.
- `ussa1976` — US Standard Atmosphere 1976 temperature / pressure
  profiles, used by the column model to set per-cell environmental
  conditions.
- `ephem` — solar position (zenith angle) from latitude / longitude
  / UTC time, used by the column model to drive TUV-x photolysis
  through the diurnal cycle.

The standalone-example sections each link back here for the install;
no need to re-run `pip` between sections.

The development qualification tree used four standalone scripts:

```bash
python scripts/musica_python/abba_box.py
python scripts/musica_python/lnox_box.py
python scripts/musica_python/chapman_nox_column.py
python scripts/musica_python/tropo_box.py
```

The fourth exercises the reduced Ox-HOx-NOx-CO-CH4 mechanism through a two-day
TUV-x-driven diurnal cycle. These commands are retained as qualification
provenance; the public MVP distributes declarative coupled examples through
the wiki rather than the development automation tree.

## Chapters

- [Chapter 2: Deep Convection (Supercell) — ABBA and Lightning NOx](02-deep-convection.md)
  — idealized deep convection, run with two MUSICA/MICM mechanisms, with
  a side-by-side comparison.
- [Chapter 3: Chapman + NOx Photostationary State](03-chapman-nox.md) —
  small-domain Chapman cycle plus NOx, where the analytical PSS solution
  is a clean numerical sanity check.
- [Chapter 4: Stratosphere — Chapman + NOx (Global)](04-stratosphere.md)
  — the same chemistry on the global `x1.40962` mesh, where the
  day–night photolysis terminator and zonal-mean ozone response become
  visible.

## Beyond the tutorial

- [Global MVP reconstruction](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions)
  — public inputs and manual staging for the No Surface Emissions,
  Anthropogenic Emissions, and Anthropogenic + Fire Emissions scenarios.
- [MVP qualification record](../chempas/mvp/MVP_PRE_RELEASE.md) — prescribed
  upper O3, reduced Ox-HOx-NOx-CO-CH4 chemistry, source attribution, and
  interpretation limits.
- [MIEM integration](../chempas/musica/MIEM_INTEGRATION.md) — exact-grid
  inventory preparation, the self-contained chem-box fixture, distributed
  runtime behavior, and global qualification evidence.
- [Global tropospheric NOx](../chempas/musica/GLOBAL_TROPOSPHERIC_NOX.md) —
  reduced and expanded chemistry promotion ladders.
- [Global tropospheric methane](../chempas/musica/GLOBAL_TROPOSPHERIC_METHANE.md)
  — post-MVP development status for signed methane exchange, initialization,
  MOZART-35, and evidence publication.

The global guides require external provider data under
`CHEMPAS_EMISSIONS_DATA_ROOT`. The small examples and synthetic fixtures must
not be substituted for that scientific forcing.

## Verifying numerically

The accepted clean-build and test matrix is recorded in
[`STAGE5_FULL_REGRESSION.md`](../chempas/mvp/STAGE5_FULL_REGRESSION.md). The
development suite and its shell harnesses are provenance for that result; they
are not shipped as commands in the public MVP source. Public users can
reconstruct the released examples from the wiki and apply the log, stream,
restart, and mass-bookkeeping checks documented in this site.
