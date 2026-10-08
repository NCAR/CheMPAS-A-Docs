# Chapter 4: Stratosphere — Chapman + NOx (Global)

```{admonition} Work in progress
:class: warning

This chapter is being actively written. Commands and expected output
are provisional; figure slots are left without rendered PNGs until the
corresponding model runs and plots are archived.
```

Chapter 3 used the supercell mesh as a column-like sandbox to verify
the Chapman + NOx mechanism against the analytical Leighton
photostationary state. This chapter runs the same chemistry on a
global mesh — the standard MPAS `x1.40962` 120 km quasi-uniform mesh —
and looks at what the diurnal cycle of solar photolysis does when it
sweeps across an entire planet: Chapman ozone chemistry with NOₓ
catalytic loss, exercised globally over a full diurnal cycle.

## 4.1 What you'll learn

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

By the end of this chapter you will:

- Run the `chapman_nox_global` idealized case on the global
  `x1.40962` mesh in CheMPAS-A.
- See the day–night photolysis terminator sweep across a global jNO₂
  field, sampled at four times during one daily sweep.
- Verify that NO/NO₂ partitioning flips across the terminator —
  daytime tracking the Leighton photostationary state introduced in
  Chapter 3, nighttime relaxing toward NO₂.
- Inspect the global-mean and zonal-mean ozone response over a
  24-hour integration.

## 4.2 The Stratosphere (Chapman + NOx global) case

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

The case runs the same `chapman_nox.yaml` MICM mechanism and
`tuvx_chapman_nox.json` photolysis configuration as Chapter 3 — six
prognostic species (O₂, O, O¹D, O₃, NO, NO₂), four photolysis rates
(jO₂, jO₃→O, jO₃→O¹D, jNO₂) — but on the global `x1.40962` mesh.
Domain summary:

- 40 962 cells, nominal 120 km spacing, 26 vertical levels (the
  standard JW baroclinic-wave initialization mesh).
- 24-hour integration, 450 s dynamics timestep, 3600 s TUV-x update
  interval.
- `config_chemistry_use_grid_coords = .true.` — every cell uses its
  own (latitude, longitude) for the solar-zenith-angle calculation,
  so jNO₂ at any instant has the day–night terminator built in.
- The TUV-x upper-atmosphere extension is enabled. The global-case CSV
  in `test_cases/chapman_nox_global/` begins at the JW model lid (45 km)
  and extends to 100 km; the supercell-specific file in Chapter 3 instead
  begins at its 50 km lid.

This case borrows the JW baroclinic-wave init mesh purely as a
convenient global initial state for the dynamics; it is not a
baroclinic-wave dynamics demonstration. The Chapman + NOx chemistry
runs on whatever flow the dynamics produce, but the dominant signal
in the chemistry diagnostics is the diurnal photolysis cycle, not
the dynamics.

**[Figure 4.1: Gaussian initial qO₃ profile (peak qO₃ = 1×10⁻⁵ kg kg⁻¹,
10 ppm by mass or about 6 ppmv, at 25 km; σ = 7 km) injected globally by
`init_chapman_nox.py`. To be added.]**

## 4.3 Setup

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

Before you run anything, confirm:

```bash
# Start in the v2026.08.01 checkout, define the run-data locations, and
# activate Python.
cd /path/to/CheMPAS-A
export CHEMPAS_ROOT="$(pwd)"
export CHEMPAS_RUN_ROOT=/path/to/CheMPAS-run-data
export CHEMPAS_TUVX_DATA=/path/to/MUSICA/configs/tuvx/data
export JW_RUN="$CHEMPAS_RUN_ROOT/jw_baroclinic_wave"
export CHAPMAN_GLOBAL_RUN="$CHEMPAS_RUN_ROOT/chapman_nox_global"
conda activate mpas

# 1. The atmosphere executable exists and is from this checkout.
ls -la "$CHEMPAS_ROOT/atmosphere_model"

# 2. The standard JW initialization and eight-rank partition exist.
ls "$JW_RUN/x1.40962.init.nc" \
   "$JW_RUN/x1.40962.graph.info.part.8"

# 3. Create the case directory and link the large, reusable inputs.
mkdir -p "$CHAPMAN_GLOBAL_RUN"
cd "$CHAPMAN_GLOBAL_RUN"
ln -sf "$JW_RUN/x1.40962.init.nc" .
ln -sf "$JW_RUN/x1.40962.graph.info.part.8" .
test -d "$CHEMPAS_TUVX_DATA"

# 4. Confirm plotting dependencies in the active environment.
python -c "import netCDF4, numpy, cartopy, matplotlib, scipy; print('ok')"
```

If the JW files are missing, extract the NCAR
[JW baroclinic-wave archive](https://www2.mmm.ucar.edu/projects/mpas/test_cases/v7.0/jw_baroclinic_wave.tar.gz)
into `$CHEMPAS_RUN_ROOT`; it unpacks to `jw_baroclinic_wave/` with the
grid and eight-rank partition. If `x1.40962.init.nc` is still missing,
copy the release's `test_cases/jw_baroclinic_wave/` files into `$JW_RUN`
and run `init_atmosphere_model` there on eight ranks (see the
[Idealized Test Cases](https://github.com/NCAR/CheMPAS-A/wiki/Idealized-Test-Cases)
guide). The release container prepares and runs this case as
`chapman-nox-global`; see
[Running the cases in a container](01-overview.md#running-the-cases-in-a-container).

Always run with 8 MPI ranks for this case — the partition file in the
run directory (`x1.40962.graph.info.part.8`) is keyed to that rank
count, and a mismatched partition file causes a segfault in the
dynamics solver.

## 4.4 Initializing Chapman + NOx tracers globally

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

The `chapman_nox_global` streams config reads
`x1.40962.chapman_nox_init.nc` — a copy of the JW init NetCDF with
five Chapman + NOx tracers injected as functions of altitude only. The sixth
mechanism tracer, `qO1D`, is runtime-created at its configured zero default.
`scripts/init_chapman_nox.py` does the injection:

```bash
cd "$CHAPMAN_GLOBAL_RUN"
python "$CHEMPAS_ROOT/scripts/init_chapman_nox.py" \
    -i x1.40962.init.nc \
    -o x1.40962.chapman_nox_init.nc
```

What the script writes:

- `qO2` — uniform 0.21 mole fraction (≈0.232 kg/kg).
- `qO3` — Gaussian peak qO₃ = 1×10⁻⁵ kg kg⁻¹ at 25 km, σ = 7 km
  (10 ppm by mass, about 6 ppmv).
  Function of altitude only; horizontal structure comes from the
  chemistry's diurnal cycle, not from the initial state.
- `qO` — small floor (1×10⁻¹²). `qO1D` is not seeded; the runtime
  default of zero is fine for a fast radical that the chemistry
  spins up to Chapman quasi-steady-state within seconds on the first
  sunlit step (consistent with Ch. 3 §3.5).
- `qNO`, `qNO2` — 1 ppbv background each, uniform with altitude.
  Lower than the stratospheric NOx peak (~10 ppb in §3.5) but
  sufficient to drive a visible terminator-aligned partition flip.

Mass mixing ratios are written in kg/kg. The scripts use mutually consistent
molar-mass approximations; a few constants differ only in their retained
decimal precision.

## 4.5 Running

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

The release's `test_cases/chapman_nox_global/` directory holds the
namelist, streams, output-variable list, and global-case extension CSV;
the wiki's
[Chemistry Test Cases](https://github.com/NCAR/CheMPAS-A/wiki/Chemistry-Test-Cases)
page documents the same case. Copy them into the run directory, then
stage the mechanism and TUV-x JSON that the namelist resolves relative
to that directory:

```bash
cd "$CHAPMAN_GLOBAL_RUN"
cp "$CHEMPAS_ROOT/test_cases/chapman_nox_global/"* .
cp "$CHEMPAS_ROOT/micm_configs/chapman_nox.yaml" .
cp "$CHEMPAS_ROOT/micm_configs/tuvx_chapman_nox.json" .
[ -e data ] || ln -s "$CHEMPAS_TUVX_DATA" data
ln -sf "$CHEMPAS_ROOT/atmosphere_model" .

# The partition file lives next to the JW init.
ln -sf "$JW_RUN/x1.40962.graph.info.part.8" .
```

The release chemistry records read:

```fortran
&chemistry
    config_micm_file = 'chapman_nox.yaml'
/

&photolysis
    config_tuvx_config_file = 'tuvx_chapman_nox.json'
    config_tuvx_top_extension = .true.
    config_tuvx_upper_column_mode = 'legacy_static'
    config_tuvx_extension_file = 'tuvx_upper_atm.csv'
    config_tuvx_update_interval = 3600.0
    config_chemistry_use_grid_coords = .true.
/
```

No `config_chemistry_latitude` / `config_chemistry_longitude` —
`use_grid_coords = .true.` overrides those, and every cell gets its
own SZA. The 3600 s TUV-x update interval is a deliberate choice
for this case; the Ch. 3 small-domain run does not set
`config_tuvx_update_interval` and falls back to the registry default
of 0.0 (TUV-x runs every chemistry step). On a 24-hour global run
the SZA evolves slowly enough that hourly TUV-x updates resolve the
terminator sweep correctly without running TUV-x on every chemistry
step.

**Archive prior output and run.** Same pattern as Chapter 2 / Chapter 3:

```bash
timestamp=$(date +%Y%m%d_%H%M%S)
[ -f output.nc ] && mv output.nc output.${timestamp}.nc
[ -f log.atmosphere.0000.out ] && \
    mv log.atmosphere.0000.out log.atmosphere.0000.${timestamp}.out

mpiexec -n 8 ./atmosphere_model
```

The 24-hour integration takes longer than the 2-hour supercell case;
expect order-tens-of-minutes wall time on a workstation, dominated by
TUV-x and dynamics rather than MICM.

Verify the run completed cleanly by checking the tail of
`log.atmosphere.0000.out`:

```
Critical error messages = 0
```

Check that the six species and four photolysis rates are present,
finite, and non-negative with the loop from Chapter 2 §2.8 and this
mapping:

```python
expected = {
    'output.nc': ['qO2', 'qO', 'qO1D', 'qO3', 'qNO', 'qNO2',
                  'j_jNO2', 'j_jO2', 'j_jO3_O', 'j_jO3_O1D'],
}
```

## 4.6 Plotting the global response

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

Plot `output.nc` with your own analysis tools; the output list carries
`latCell`, `lonCell`, and `zgrid` alongside the chemistry fields. For
maps, triangulate the cell centers and mask antimeridian-spanning
triangles so the limb is clean. These figures show the global response:

- **NO at 25 km** — a single 25 km NO map at 12 UTC with the terminator
  overlaid, emphasizing the dayside photolysis product.

- **NO₂ at 25 km** — the matching NO₂ reservoir map, including its
  daylight drawdown.

- **NO and NO₂ contours** — overlaid NO and NO₂ fields at the same level
  and time, with separate color scales and the terminator.

- **jNO₂ terminator sweep** — jNO₂ maps at t = 3, 9, 15, 21 UTC.
  The day–night terminator is shown at four snapshots during one daily sweep,
  visible as a sharp drop in jNO₂ at the photolysis edge. (t = 0 is skipped
  because TUV-x has not yet fired at the initial output frame, so jNO₂ is
  identically zero there.)

  **[Figure 4.2: jNO₂ terminator-sweep map at t = 3 / 9 / 15 / 21
  UTC. To be added.]**

- **Tracer evolution** — qO₃ at level 22 (≈36 km, where the Chapman
  cycle is most active) and qNO₂ at a representative level 17 (≈25 km),
  shown at t = 12 h and t = 24 h. Initial NO and NO₂ are uniform with
  altitude, so this is not a seeded NOx peak. These level indices are
  tied to the JW 26-level grid; if the vertical grid changes, pick new
  levels.

  **[Figure 4.3: qO₃ at ≈36 km and qNO₂ at ≈25 km, t = 12 h and t =
  24 h. To be added.]**

- **NO₂ partition** — NO₂ / (NO + NO₂) molar fraction at t = 12 h
  and t = 24 h. Dayside drops toward Leighton (lower fraction —
  jNO₂ converts NO₂ → NO); nightside relaxes toward NO₂ (higher
  fraction — no photolysis, NO + O₃ titrates NO back to NO₂).

  **[Figure 4.4: NO₂ partition fraction at t = 12 h and t = 24 h. To
  be added.]**

- **O₃ profile** — global-mean O₃ vertical profile and the
  zonal-mean ΔO₃ over the 24-hour window. Symmetric-log color norm so
  upper-stratosphere production above ~30 km and lower-altitude
  NOx-driven loss below are both visible in the same figure.

  **[Figure 4.5: Global-mean O₃ profile and zonal-mean ΔO₃ over 24 h.
  To be added.]**

The next two figures were made from hourly output of this case covering
2026-06-24 UTC. The release namelist
starts at `0000-01-01_00:00:00` instead; if you convert `xtime` with
Python's `datetime`, note that it cannot represent year 0000.

- **Ozone zonal mean** — the zonal-mean O₃ pressure–latitude cross
  section, averaged over a full UTC day, beside latitude-band O₃
  profiles sharing the pressure axis. Columns are interpolated to a
  common log-pressure grid and lightly smoothed.

  ```{figure} ../_static/o3_zonal_mean.png
  :name: fig-stratosphere-o3-zonal-mean
  :alt: Zonal-mean O3 pressure-latitude cross-section with latitude-band profiles.
  :width: 100%

  Figure 4.6: Zonal-mean O₃ from 2026-06-24 output.
  Left: day-averaged zonal-mean O₃ as a pressure–latitude
  cross-section. Right: O₃ profiles for representative latitude bands
  on the shared pressure axis. The ozone maximum sits in the middle
  stratosphere, with the expected latitudinal structure of the Chapman
  layer.
  ```

- **NOₓ diurnal cycle** — a Hovmöller of the NO₂/NOₓ partition
  (pressure vs. Mountain Standard Time) in the Boulder column, beside
  NO and NO₂ profiles at local noon.

  ```{figure} ../_static/nox_diurnal.png
  :name: fig-stratosphere-nox-diurnal
  :alt: Hovmoller of the NO2/NOx partition over a diurnal cycle in the Boulder column.
  :width: 100%

  Figure 4.7: NOₓ diurnal cycle from 2026-06-24 output.
  Left: Hovmöller of the NO₂/NOₓ partition fraction (pressure vs. MST)
  in the Boulder column — daytime photolysis drives the partition
  toward NO, nighttime relaxes it back toward NO₂. Right: NO and NO₂
  profiles at local noon.
  ```

## 4.7 What to look for

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

Three diagnostics worth checking by eye:

- **Terminator alignment.** In the jNO₂ terminator maps (Figure 4.2),
  the jNO₂ drop should align with the geometric SZA = 90° great circle
  at each UTC hour. If the terminator is rotated or offset, the
  `use_grid_coords` machinery is mis-wired.
- **Partition flip.** In the NO₂ partition maps (Figure 4.4), daytime
  hemispheres should sit at lower NO₂ fractions than nighttime
  hemispheres. The contrast tracks where the integration is in its
  diurnal cycle — t = 12 h and t = 24 h are 12 hours apart and show
  approximately opposite day/night phases at the prime meridian.
- **Ozone modulation magnitude.** In the tracer-evolution and O₃
  profile figures (Figures 4.3 and 4.5), expect a small diurnal
  modulation in qO₃ at 36 km, visible as a difference between the
  t = 12 h and t = 24 h panels. The 24-hour integration is too short
  for the column to fully relax; longer runs (multi-day, outside the
  scope of this chapter) would show a slow drift toward the steady
  state.

The fast-radical species (qO, qO¹D) should stay small everywhere
once chemistry has spun up — they are output for diagnostic value
but should not exceed parts-per-billion levels in the column.

## 4.8 Next steps and see also

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

- **The Leighton photostationary state** that this chapter shows
  flipping across the terminator is verified analytically on a small
  domain in
  [Chapter 3 §3.7–§3.8](03-chapman-nox.md). Chapter 3 is the right
  next stop if the partition behaviour here surprises you.
- **The MUSICA/MICM coupling internals** are documented in
  [MUSICA integration](../chempas/musica/MUSICA_INTEGRATION.md).
- **TUV-x integration engineering** — the column extension, host
  profile updates, and the `use_grid_coords` machinery — is
  documented in
  [TUV-x integration](../chempas/guides/TUVX_INTEGRATION.md).
- **The LNOx scheme** — both gating modes, namelist surface, and
  calibration notes — is documented in
  [LNOx integration](../chempas/guides/LNOX_INTEGRATION.md).
  The global Chapman + NOx case has no LNOx source, but readers
  exploring chemistry-coupled cases should see the LNOx scheme too.
- **Upstream MUSICA, MICM, and TUV-x docs** are linked from the
  [project landing page](../index.rst) in the *See also* section.
