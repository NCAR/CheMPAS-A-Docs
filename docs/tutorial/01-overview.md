# Chapter 1: Overview

The CheMPAS-A Tutorial walks through CheMPAS-A's idealized chemistry test
cases. Where the [User's Guide](../users-guide/index.rst) is a reference-style
CheMPAS-A adaptation of the upstream MPAS-Atmosphere documentation, this
tutorial is narrative: run the case, look at the output, understand what the
chemistry is doing.

The tutorial cases are teaching examples. For global chemistry with surface
emissions, use the public guides linked under
[Beyond the tutorial](#beyond-the-tutorial) rather than treating an idealized
case as production forcing.

## What this tutorial assumes

- A checkout of the CheMPAS-A
  [v2026.08.01 release](https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01),
  for example from
  `git clone --branch v2026.08.01 https://github.com/NCAR/CheMPAS-A.git`.
  Its `micm_configs/`, `scripts/`, and `test_cases/` directories hold the
  mechanisms, TUV-x configurations, tracer initializers, and case
  configurations used in Chapters 2--4. The examples call this checkout
  `$CHEMPAS_ROOT`.
- `atmosphere_model` is built. See the
  [build guide](https://github.com/NCAR/CheMPAS-A/wiki/Building) and
  [Chapter 3 of the User's Guide](../users-guide/03-building.md).
- A separate run-data root is set up with each case's namelist, streams,
  graph partition, and (where needed) initial-condition files. The examples
  call this location `$CHEMPAS_RUN_ROOT`; each chapter names the NCAR
  test-case archive and release `test_cases/` directory it uses. Further
  public inputs are in the
  [examples wiki](https://github.com/NCAR/CheMPAS-A/wiki/Examples).
- The conda environment `mpas` is available for plotting:
  `conda activate mpas`.
- For coupled TUV-x runs, `CHEMPAS_TUVX_DATA` points to a MUSICA source
  checkout's `configs/tuvx/data` directory. Chapters 2--4 stage that tree as
  `data` in each run directory because the TUV-x JSON paths are relative.

## Running the cases in a container

The release's
[`docker/README.md`](https://github.com/NCAR/CheMPAS-A/blob/v2026.08.01/docker/README.md)
describes a Docker build and run harness for three of the tutorial cases:
`supercell-abba` (Supercell ABBA, §2.5), `supercell-lnox` (Supercell
LNOx + O3, §2.6), and `chapman-nox-global` (Global Chapman + NOx,
Chapter 4). The image builds `init_atmosphere_model` and `atmosphere_model`
with MUSICA/MICM support. Its Python environment contains only NumPy and
netCDF4, so plot the output on the host. The supported container target is
Linux/AMD64.

From the root of the release checkout, build the image, create a host data
directory, and run a case:

```bash
docker build --platform linux/amd64 \
  -f docker/Containerfile --target run -t chempas-a:docker .

mkdir -p "$HOME/Data/CheMPAS"

docker run --rm \
  --platform linux/amd64 \
  --shm-size=1g \
  -v "$HOME/Data/CheMPAS:/data/CheMPAS" \
  chempas-a:docker supercell-abba
```

Replace `supercell-abba` with `supercell-lnox` or `chapman-nox-global` for
the other two cases. The runner downloads missing NCAR MPAS v7.0 test-case
archives and writes each case to its own directory under
`$HOME/Data/CheMPAS`. The `--shm-size=1g` allocation is required by the
eight-rank OpenMPI runs. After a run, the harness checks that `output.nc`
and `log.atmosphere.0000.out` exist, that the log reports
`Critical error messages = 0`, and that the expected chemistry variables are
present and finite. The README also covers setup-only runs and the
`CHEMPAS_FORCE_INIT` and `CHEMPAS_RUN_DURATION` overrides.

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

Chapter 2 reproduces the standalone ABBA box script in full (§2.10).
Sections 2.11 and 3.10 describe the corresponding single-cell LNOx + O₃ box
and Chapman + NOx column calculations.

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

- [Global chemistry and emissions](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions)
  — public inputs and manual staging for the No Surface Emissions,
  Anthropogenic Emissions, and Anthropogenic + Fire Emissions scenarios.
- [MIEM integration](../chempas/musica/MIEM_INTEGRATION.md) — exact-grid
  inventory preparation, the self-contained chem-box fixture, and
  distributed runtime behavior.

The global guides require external provider data under
`CHEMPAS_EMISSIONS_DATA_ROOT`. The small examples and synthetic fixtures must
not be substituted for that scientific forcing.

## Verifying numerically

Each chapter ends with checks to apply to your own output: a rank-zero log
that reports `Critical error messages = 0`, the expected chemistry and
photolysis fields present, finite, and non-negative, and case-specific
diagnostics such as the Leighton photostationary-state comparison in
Chapter 3.
