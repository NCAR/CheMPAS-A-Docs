# Chapter 2: Deep Convection (Supercell) — ABBA and Lightning NOx

## 2.1 What you'll learn

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

By the end of this chapter you will:

- Run the supercell idealized **deep convection** case in CheMPAS-A.
- Switch between two MUSICA/MICM chemistry mechanisms — the toy ABBA
  reactant set and the LNOx + O3 lightning-NOx tropospheric setup (the
  Deep Convection chemistry case) — by editing the chemistry namelist records
  block.
- Compare what tracer transport looks like in isolation (ABBA) against
  what it looks like coupled to active gas-phase chemistry and a
  lightning-NOx source (LNOx + O3).

## 2.2 The supercell case

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

The supercell test case is an idealized deep-convection setup adapted
from Weisman and Klemp (1982): a horizontally homogeneous, strongly
sheared environment perturbed by a warm bubble that triggers a
long-lived rotating storm. CheMPAS-A's tracked configuration
uses 60 stretched vertical levels spanning 0–50 km (~300 m at the
surface, ~1 km near the lid), a 3-second dynamics timestep, Kessler
warm-rain microphysics, and a 2-hour integration.

It is a useful chemistry testbed for two reasons. First, the rotating
updraft produces strong, well-organized vertical transport that lifts
boundary-layer tracers into the upper troposphere; the cold-pool
outflow then spreads species horizontally near the surface. Second,
the dynamics are deterministic and the chemistry adds no feedback to
the dynamics — which means a chemistry change shows up cleanly as a
chemistry-only signal, rather than confounded with a different storm
evolution.

**[Figure 2.1: Supercell initial state — potential temperature and
moisture cross-section. To be added.]**

## 2.3 Setup checklist

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

Before you run anything, confirm:

```bash
# Start in the CheMPAS-A checkout and keep source and run data separate.
cd /path/to/CheMPAS-A-qualification
export CHEMPAS_ROOT="$(pwd)"
export CHEMPAS_RUN_ROOT=/path/to/CheMPAS-run-data
export CHEMPAS_TUVX_DATA=/path/to/MUSICA/configs/tuvx/data
export SUPERCELL_RUN="$CHEMPAS_RUN_ROOT/supercell"
conda activate mpas

# 1. The executables exist and are from this checkout.
ls -la "$CHEMPAS_ROOT/atmosphere_model" \
       "$CHEMPAS_ROOT/init_atmosphere_model"

# 2. The downloaded supercell data and tracked configuration are staged.
cd "$SUPERCELL_RUN"
ls supercell_grid.nc supercell.graph.info.part.8 \
   namelist.atmosphere streams.atmosphere \
   stream_list.atmosphere.output \
   namelist.init_atmosphere streams.init_atmosphere \
   supercell_zeta_levels.txt
test -d "$CHEMPAS_TUVX_DATA"

# 3. The active Python environment has the analysis dependencies.
python -c "import netCDF4, numpy, matplotlib, scipy; print('ok')"
```

Keep these variables set for the remaining commands in Chapters 2 and 3.
If any check fails, see
the public MVP [build guide](https://github.com/NCAR/CheMPAS-A/wiki/Building)
for the model build,
[Getting Started](https://github.com/NCAR/CheMPAS-A/wiki/Getting-Started) for
the run-directory layout, and
[Idealized Test Cases](https://github.com/NCAR/CheMPAS-A/wiki/Idealized-Test-Cases)
for data download and public configuration staging.

## 2.4 Initialization

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

If `supercell_init.nc` is already in the run directory, you can skip
ahead to running the model. To regenerate the initial condition from
scratch:

```bash
cd "$SUPERCELL_RUN"
mpiexec -n 8 "$CHEMPAS_ROOT/init_atmosphere_model"
```

This produces `supercell_init.nc`, which contains the prognostic state
on the unstructured Voronoi mesh, the stretched vertical levels read
from `supercell_zeta_levels.txt`, and the Kessler microphysics
variables.

Always run with 8 MPI ranks for the supercell case — the partition
file in the run directory (`supercell.graph.info.part.8`) is keyed to
that rank count, and a mismatched partition file causes a segfault in
the dynamics solver. See `RUN.md` in the repository root for the full
rank-vs-partition table.

## 2.5 Run with the ABBA mechanism

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

The ABBA mechanism (`micm_configs/abba.yaml`) is a reversible three-species
toy reaction--transport test: qAB ⇌ qA + qB. The forward rate is
2 × 10⁻³ s⁻¹, an initial chemical timescale of 500 s, so chemistry
substantially repartitions qAB into qA = qB during the first tens of minutes
while the supercell deforms and transports all three tracers. The reverse
step is bimolecular. CheMPAS-A converts q cell by cell as
`[X] = qX * rho_dry / M_X`, so the local equilibrium depends on density and
tracer loading.

**Initialize the ABBA tracer.** Give qAB a horizontal sine pattern so
the supercell flow has something to advect (without this step, qAB is
uniform and the resulting plot has no structure):

```bash
cd "$SUPERCELL_RUN"
cp "$CHEMPAS_ROOT/micm_configs/abba.yaml" .
python "$CHEMPAS_ROOT/scripts/init_tracer_sine.py" \
    -i supercell_init.nc -t qAB --create \
    --waves-x 2 --amplitude 0.4 --offset 0.6
```

This sets qAB to a nominal 0.2--1.0 sine pattern with mean 0.6:
two cycles in x multiplied by the script's default one cycle in y.

**Edit the namelist.** Open `$SUPERCELL_RUN/namelist.atmosphere`, remove any
previous `&photolysis` and `&lnox` records, and leave this chemistry block:

```fortran
&chemistry
    config_micm_file = 'abba.yaml'
/
```

ABBA does not need TUV-x photolysis or the lightning-NOx options, so
the block is minimal.

**Archive any prior output and run.** MPAS defaults to
`clobber_mode = never_modify`; if `output.nc` already exists the run
will silently skip all output writes. Always move the previous output
aside before re-running:

```bash
cd "$SUPERCELL_RUN"

timestamp=$(date +%Y%m%d_%H%M%S)
[ -f output.abba.nc ] && mv output.abba.nc output.abba.${timestamp}.nc
[ -f log.abba.out ] && mv log.abba.out log.abba.${timestamp}.out
[ -f output.nc ] && mv output.nc output.${timestamp}.nc
[ -f log.atmosphere.0000.out ] && \
    mv log.atmosphere.0000.out log.atmosphere.0000.${timestamp}.out

mpiexec -n 8 "$CHEMPAS_ROOT/atmosphere_model"

# Give this run stable names before changing mechanisms.
[ -f output.nc ] && mv output.nc output.abba.nc
[ -f log.atmosphere.0000.out ] && mv log.atmosphere.0000.out log.abba.out
```

**Verify the run completed cleanly.** The tail of
`log.abba.out` should report zero critical errors:

```
Critical error messages = 0
```

**Plot.** With the conda env active:

```bash
mkdir -p plots
python "$CHEMPAS_ROOT/scripts/plot_abba_supercell.py" \
    -i output.abba.nc --outdir plots --kind cross --y-slice 18
```

The command writes `plots/abba_supercell_qAB.{png,pdf}` and
`plots/abba_supercell_qA.{png,pdf}`.

```{figure} ../_static/abba_supercell_qAB.png
:name: fig-abba-supercell-qab
:alt: Vertical cross-section of qAB through the supercell at t = 2 h.
:width: 100%

Figure 2.2a: qAB cross-section through the supercell storm (y = 18 km) at
t = 2 h. The initial horizontal sine pattern is deformed by the updraft and
cold-pool outflow while reversible chemistry depletes the reservoir.
```

```{figure} ../_static/abba_supercell_qA.png
:name: fig-abba-supercell-qa
:alt: Vertical cross-section of qA = qB through the supercell at t = 2 h.
:width: 100%

Figure 2.2b: qA (= qB by symmetry) cross-section at the same slice and time
— the dissociation product, grown from zero where qAB has reacted and then
transported with the storm.
```

What to look for: qAB is both advected and chemically depleted, while qA
and qB grow to substantial values and are transported by the same flow.
Their spatially varying partition reflects both storm transport and the
density-dependent reversible chemistry. qA and qB remain equal by symmetry.

## 2.6 Deep Convection: the Lightning NOx + O₃ mechanism

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

The LNOx + O3 setup (`micm_configs/lnox_o3.yaml`) is a tropospheric
gas-phase configuration with three prognostic species — NO, NO₂, and
O₃ — and a parameterized lightning-NOx source term. It is the
smallest realistic chemistry case in CheMPAS-A: enough species and
reactions to exercise the MICM solver, TUV-x photolysis, and the LNOx
source coupling, without the cost of a full tropospheric mechanism.

```{figure} ../_static/lightning_nox_noxcross_t040min.png
:name: fig-deep-convection-noxcross
:alt: Deep Convection vertical cross-section of Lightning NOx at t = 40 min.
:width: 100%

Figure 2.3: Deep Convection vertical cross-section at y = 46 km,
t = 40 min. Left: Lightning NOₓ (ppbv, filled) through the storm, with
liquid-water-content contours (teal) outlining the cloud and ΔO₃
contours (gray) marking O₃ depleted by NO titration in the fresh
plume. Center: column profiles of NOₓ (mean and min–max envelope), the
NO₂/NOₓ partitioning ratio, and the photolysis rate jNO₂. Right: the
parameterized LNOₓ source profile. NOₓ is lofted into the 8–11 km
anvil where the updraft is strongest.
```

The lightning-NOx source has two gating modes, configurable through
the `&lnox` namelist:

- **Altitude-mode** gating (the inherited DAVINCI-MPAS formulation) —
  emit NO in a fixed altitude window, with rate scaled by updraft
  excess.
- **Isotherm-mode** gating (new, faithful to the DC3 mixed-phase
  framing in `LNOx.md`) — emit NO in a temperature window
  corresponding to the 233–262 K layer, at a constant rate.

This section walks through both modes as parallel runs and then
compares them. The full scheme description, namelist surface, and
calibration notes live in the
[LNOx integration guide](../chempas/guides/LNOX_INTEGRATION.md).

**Initialize the LNOx tracers.** The supercell init file does not
contain NO / NO₂ / O₃; populate them with a one-time script. Both
gating modes use the same initial state:

```bash
cd "$SUPERCELL_RUN"
cp "$CHEMPAS_ROOT/micm_configs/lnox_o3.yaml" .
cp "$CHEMPAS_ROOT/micm_configs/tuvx_no2.json" .
cp "$CHEMPAS_ROOT/micm_configs/tuvx_upper_atm.csv" .
[ -e data ] || ln -s "$CHEMPAS_TUVX_DATA" data
python "$CHEMPAS_ROOT/scripts/init_lnox_o3.py" -i supercell_init.nc
```

This sets NO = 0, NO₂ = 0, and O₃ = 50 ppbv (background) throughout
the domain. Add `j_jNO2` as its own line in
`stream_list.atmosphere.output`; photolysis diagnostics are injected at
runtime and therefore are not covered by the static stream list alone.

### 2.6.1 LNOx with altitude-mode gating

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

**Edit the namelist.** Replace the chemistry records in
`namelist.atmosphere` with the altitude-mode configuration:

```fortran
&chemistry
    config_micm_file = 'lnox_o3.yaml'
/

&photolysis
    config_tuvx_config_file = 'tuvx_no2.json'
    config_tuvx_top_extension = .true.
    config_tuvx_upper_column_mode = 'legacy_static'
    config_tuvx_extension_file = 'tuvx_upper_atm.csv'
    config_tuvx_update_interval = 600.0
    config_j_no2_max = 0.01
    config_chemistry_latitude = 35.86
    config_chemistry_longitude = -97.93
/

&lnox
    config_lnox_gating_mode = 'altitude'
    config_lnox_source_rate = 0.5
    config_lnox_w_threshold = 5.0
    config_lnox_w_ref = 10.0
    config_lnox_z_min = 5000.0
    config_lnox_z_max = 12000.0
    config_lnox_nox_tau = 0.0
/
```

With `config_tuvx_config_file` active, TUV-x supplies `j_jNO2` and
`config_j_no2_max` is ignored. The latter is retained only for the Phase 1
no-TUV-x fallback path.

In altitude mode, NO is injected into grid cells where the vertical
velocity exceeds `config_lnox_w_threshold` and the height falls
between `config_lnox_z_min` and `config_lnox_z_max`. The per-cell
emission rate is `S = source_rate · (w − w_threshold) / w_ref`, so
stronger updrafts emit more NO.

**Archive prior output and run.** Same pattern as the ABBA run:

```bash
timestamp=$(date +%Y%m%d_%H%M%S)
[ -f output.altitude.nc ] && \
    mv output.altitude.nc output.altitude.${timestamp}.nc
[ -f log.altitude.out ] && mv log.altitude.out log.altitude.${timestamp}.out
[ -f output.nc ] && mv output.nc output.${timestamp}.nc
[ -f log.atmosphere.0000.out ] && \
    mv log.atmosphere.0000.out log.atmosphere.0000.${timestamp}.out

mpiexec -n 8 "$CHEMPAS_ROOT/atmosphere_model"

# Name the altitude-mode artifacts so they survive the §2.6.2 run.
[ -f output.nc ] && mv output.nc output.altitude.nc
[ -f log.atmosphere.0000.out ] && mv log.atmosphere.0000.out log.altitude.out
```

**Plot.** The dedicated LNOx plotting script is intended to produce the standard
diagnostic set (vertical cross-sections, time series, NO₂
partitioning ratio):

```{admonition} Known plotting limitation
:class: warning

Verified with Matplotlib 3.11.0 in the current `mpas` environment,
`plot_lnox_o3.py` fails during module import, before argument parsing, and
writes no plots:

`ValueError: the values passed in the (value, color) pairs must increase monotonically from 0 to 1.`

The custom colormap repeats the `0.10` stop. This does not affect the model
run or the output-validation commands in §2.8.
```

```bash
python "$CHEMPAS_ROOT/scripts/plot_lnox_o3.py" \
    -i output.altitude.nc -o lnox_altitude.png
```

**[Figure 2.4: NO, NO₂, O₃ at t = 2 h, LNOx + O3 mechanism, altitude
gating. To be added.]**

What to look for: a localized NO source in the updraft column where
the vertical-velocity threshold is exceeded, downwind transport of
NO + NO₂ along the anvil, and an O₃ depletion signature in the freshly
emitted plume (titration by NO). The injected volume is a fixed
5–12 km altitude band — a slab whose location does not move with the
storm thermal structure.

### 2.6.2 LNOx with isotherm-mode gating

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

**Edit the namelist.** Replace the chemistry records with the isotherm
configuration:

```fortran
&chemistry
    config_micm_file = 'lnox_o3.yaml'
/

&photolysis
    config_tuvx_config_file = 'tuvx_no2.json'
    config_tuvx_top_extension = .true.
    config_tuvx_upper_column_mode = 'legacy_static'
    config_tuvx_extension_file = 'tuvx_upper_atm.csv'
    config_tuvx_update_interval = 600.0
    config_j_no2_max = 0.01
    config_chemistry_latitude = 35.86
    config_chemistry_longitude = -97.93
/

&lnox
    config_lnox_gating_mode = 'isotherm'
    config_lnox_source_rate = 1.0e-3
    config_lnox_w_threshold = 5.0
    config_lnox_t_min = 233.15
    config_lnox_t_max = 262.15
    config_lnox_nox_tau = 0.0
/
```

Here too, active TUV-x supplies `j_jNO2`; `config_j_no2_max` is only the
no-TUV-x fallback and does not cap the TUV-x rate.

In isotherm mode, NO is injected into grid cells where the cell
temperature is between `config_lnox_t_min` and `config_lnox_t_max`
*and* the updraft exceeds `config_lnox_w_threshold`. The emission
rate is constant: `S = source_rate` whenever the gate is open.
`source_rate = 1.0e-3 ppbv/s` is the calibration starting point in
`LNOX_INTEGRATION.md`; expect to retune by a small factor after the
first run.

**Run, then name the artifacts.** §2.6.1 already left
`output.altitude.nc` in place; this run produces `output.isotherm.nc`
so §2.6.3 can read both side-by-side:

```bash
timestamp=$(date +%Y%m%d_%H%M%S)
[ -f output.isotherm.nc ] && \
    mv output.isotherm.nc output.isotherm.${timestamp}.nc
[ -f log.isotherm.out ] && mv log.isotherm.out log.isotherm.${timestamp}.out

mpiexec -n 8 "$CHEMPAS_ROOT/atmosphere_model"

# Name the isotherm-mode artifacts so the §2.6.3 comparison can read both.
[ -f output.nc ] && mv output.nc output.isotherm.nc
[ -f log.atmosphere.0000.out ] && mv log.atmosphere.0000.out log.isotherm.out
```

**Plot.** The same import-time Matplotlib 3.11.0 limitation described in
§2.6.1 currently blocks this command as well; once corrected, point the
script at the isotherm output:

```bash
python "$CHEMPAS_ROOT/scripts/plot_lnox_o3.py" -i output.isotherm.nc \
    -o lnox_isotherm.png
```

**[Figure 2.5: NO, NO₂, O₃ at t = 2 h, LNOx + O3 mechanism, isotherm
gating. To be added.]**

What to look for: NO emission confined to the 233–262 K mixed-phase
layer of the storm — approximately mid-troposphere on the
Weisman–Klemp sounding used here — but moving with the cloud rather
than pinned to a fixed altitude.
The peak NOx in the convective core should be of order 1 ppbv (the
LNOx.md DC3 target). If your peak is off by more than a factor of a
few, retune `config_lnox_source_rate` and re-run.

### 2.6.3 Comparing the gating modes

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

Placing the two LNOx runs side by side highlights what the gating
choice changes. Spatially, altitude mode emits into a fixed slab
(`z_min`–`z_max`), so the NO source volume is the same regardless of
where the storm thermal structure sits; isotherm mode emits into the
mixed-phase layer, so the source volume shifts vertically as the
storm evolves and the 233–262 K layer moves up or down. In rate, the
altitude formulation scales with updraft excess so the strongest
updrafts emit the most NO; the isotherm formulation is flat — once
the gate is open, every active cell emits at the same rate, faithful
to the LNOx.md "constant emission" framing.

The downwind chemistry the two formulations imply — NO + O₃
titration, NO₂ photolysis, anvil-level NOx redistribution — is
identical because the MICM mechanism and TUV-x configuration are the
same; only the emission gating differs.

**[Figure 2.6: Side-by-side qNO, qNO₂, qO₃ final-state cross-sections
at t = 2 h: altitude mode (left column) vs. isotherm mode (right
column). To be added.]**

## 2.7 Comparing the two runs

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

("LNOx + O3" in this section refers to either gating mode — the
ABBA vs. LNOx contrast applies the same way to both.)
Both runs are reaction--transport problems. ABBA starts with a domain-wide
patterned reservoir and reversibly partitions it into products as all three
species are carried by the flow. LNOx starts from background O₃ and
localizes new NO in the updraft, then photochemically partitions NOx and
titrates O₃. Running both under the same dynamics shows how transport and
chemistry combine in a reversible bulk-partitioning case versus a localized,
source-driven case.

**[Figure 2.7: Side-by-side comparison of ABBA tracer transport and
LNOx + O3 chemistry at t = 2 h. To be added.]**

## 2.8 Verifying numerically

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

Visual agreement is reassuring but not sufficient. Validate each output with
the maintained checker from the active environment:

```bash
cd "$SUPERCELL_RUN"

python "$CHEMPAS_ROOT/scripts/check_chem_output.py" output.abba.nc \
  --require qA qB qAB --conserve qA+qB+qAB --nonneg

python "$CHEMPAS_ROOT/scripts/check_chem_output.py" output.altitude.nc \
  --require qNO qNO2 qO3 j_jNO2 --nonneg

python "$CHEMPAS_ROOT/scripts/check_chem_output.py" output.isotherm.nc \
  --require qNO qNO2 qO3 j_jNO2 --nonneg

grep 'Critical error messages = 0' \
  log.abba.out log.altitude.out log.isotherm.out
```

These commands check all three stable tutorial artifacts and their rank-zero
logs.

From the repository root, the maintained source-level suite is:

```bash
cd "$CHEMPAS_ROOT"
python -m unittest discover -v
scripts/test_global_tropo_f0.sh
```

The executable-backed E0 suite also carries `supercell_abba` and
`supercell_lightning` cases. Their frozen artifacts each cover exactly
`00:01:00`, so they are short compatibility and bitwise-regression gates,
not validation of the tutorial's two-hour integrations. Run them when the
external baseline bundle named by `test_cases/miem_disabled_baselines.json`
is available:

```bash
scripts/test_miem_disabled_baselines.sh . \
  --case supercell_abba --case supercell_lightning
```

The accepted clean-build matrix and all 16 maintained shell contracts are
recorded in [MVP Stage 5](../chempas/mvp/STAGE5_FULL_REGRESSION.md).

## 2.9 Next steps

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

- **The next chapter** is
  [Chapman + NOx Photostationary State](03-chapman-nox.md) — a small
  domain where the analytical PSS solution is a clean check on the
  coupled MICM + TUV-x configuration. Chapter 4 then runs the same
  chemistry on the global `x1.40962` mesh:
  [Stratosphere — Chapman + NOx (Global)](04-stratosphere.md).
- **The MUSICA/MICM coupling internals** are documented in
  [MUSICA integration](../chempas/musica/MUSICA_INTEGRATION.md).
- **The LNOx scheme** — both gating modes, full namelist surface,
  and calibration notes — is documented in
  [LNOx integration](../chempas/guides/LNOX_INTEGRATION.md).
- **TUV-x photolysis** configuration is documented in
  [TUV-x integration](../chempas/guides/TUVX_INTEGRATION.md).
- **Upstream MUSICA, MICM, and TUV-x docs** are linked from the
  [project landing page](../index.rst) in the *See also* section.

## 2.10 Standalone ABBA box model

The same mechanism as §2.5, exercised in pure Python with no MPAS in
the loop. `scripts/musica_python/abba_box.py` loads
`micm_configs/abba.yaml` into a single-cell MICM solver, seeds AB at
1 ppm, runs the reversible reaction for 2 hours, and writes
`abba_box.nc`, `abba_box.png` (300 dpi), and `abba_box.pdf` next to
the script. Useful for poking at initial conditions or temperatures
without rebuilding MPAS.

The coupled test initializes qAB nominally from 0.2--1.0 kg kg⁻¹ and converts each cell
to concentration as [AB] = qAB ρdry / 0.058. Its concentration and
equilibrium therefore vary strongly with height and tracer loading; it does
not work at one uniform reference concentration. The standalone box instead
starts at [AB] ≈ 4.46 × 10⁻⁵ mol m⁻³ at 273 K and 101 325 Pa. Because the
reverse A + B → AB step is second order, the script boosts its runtime
multiplier by about 2.2 × 10⁴. This reproduces the equilibrium *fractions*
of a chosen 1 mol m⁻³ reference box while leaving the first-order forward
multiplier at 1.0.

Pre-req: see Chapter 1's [Python environment for standalone
examples](01-overview.md) section.

Run:

```bash
cd "$CHEMPAS_ROOT"
python scripts/musica_python/abba_box.py
```

The script writes `scripts/musica_python/abba_box.nc`,
`scripts/musica_python/abba_box.png`, and
`scripts/musica_python/abba_box.pdf`.

```{figure} ../_static/abba_box.png
:name: fig-abba-box
:alt: A, B, and AB mixing ratios from the standalone ABBA box model.
:width: 100%

Figure 2.8: AB and A mixing ratios (ppm) from the standalone ABBA box
model over a 2 h integration. AB decays from 1 ppm to ≈ 0.27 ppm while
A rises to ≈ 0.73 ppm. B is omitted because A = B exactly by symmetry;
the single "A = B" curve stands for both.
```

What to look for: AB drops from 1 ppm toward the analytical
equilibrium (AB ≈ 0.27 ppm, A = B ≈ 0.73 ppm) within the first ~30
minutes of the run; the rest of the 2 h sits at steady state. A and B
are equal at every step (A = B by symmetry), so the figure plots a
single "A = B" curve. This zero-dimensional reference isolates the
reversible kinetics; the coupled test in §2.5 reacts while advection and
cell-varying density also shape the fields.

**Source listings.** Both files are reproduced inline below for
reference; they are the same files used by the script invocation
above.

```{literalinclude} ../_downloads/tutorial/abba_box.py
:caption: scripts/musica_python/abba_box.py
:language: python
:linenos:
```

The script imports the MUSICA bindings (`MICM`, the mechanism-config
parser, `SolverState`) plus `numpy`, `xarray`, and `matplotlib` for
I/O and plotting, and the project's `scripts/style.py` for
NCAR-palette plotting. After parsing `abba.yaml`, it constructs a
Rosenbrock standard-order solver, creates a single-cell state at
T = 273 K and P = 101 325 Pa, and seeds A = B = 0, AB = 1 ppm (the
ppm seed is converted to a mol m⁻³ concentration internally via
VMR = nRT / P before being handed to MICM).

The two `USER.<reaction-name>` rate parameters are *multipliers* on
the YAML `scaling factor`; the effective rate is
USER × scaling_factor. The forward reaction AB → A + B is first
order, so its multiplier stays 1.0, giving k_fwd = 2 × 10⁻³ s⁻¹ — the
same value the MPAS-coupled run sees in §2.5. The reverse reaction
A + B → AB is second order (k_rev has units m³ mol⁻¹ s⁻¹), so its
rate scales with concentration². To preserve the equilibrium
fractions while running at ~1 ppm rather than the chosen 1 mol m⁻³
reference, the script
scales the reverse multiplier up by `to_ppm / AB_INIT_PPM` (≈ 2.2 ×
10⁴ at the reference T and p). This keeps the equilibrium constant
K = k_fwd / k_rev proportional to the total mass, which is what makes
the fractional partitioning concentration-independent. The
integration loop runs for 7 200 s with a 60-second output cadence;
the inner `while elapsed < dt_out` drives MICM through whatever
sub-stepping the solver chooses while ensuring each output sample
lands exactly on the cadence.

Output is written next to the script: `abba_box.nc` (xarray Dataset
with `time` in minutes and species in mol m⁻³), `abba_box.png` (300
dpi mixing-ratio time series in ppm, converted via VMR = nRT / P), and
`abba_box.pdf` (the same figure as vector graphics).

```{literalinclude} ../_downloads/tutorial/abba.yaml
:caption: micm_configs/abba.yaml
:language: yaml
:linenos:
```

The mechanism declares three gas-phase species (`A`, `B`, `AB`) and
a single `gas` phase that lists them. Each species declaration
carries CheMPAS-A extension fields under `__`-prefixed keys
(`do advect`, `absolute tolerance`, `molar mass`,
`initial concentration`); these are non-standard and are read by the
CheMPAS-A chemistry coupler to wire each species into MPAS's tracer
transport.

The mechanism declares exactly two `USER_DEFINED` reactions: AB → A + B
with `scaling factor: 2.0e-3` and A + B → AB with
`scaling factor: 1.0e-3`. `USER_DEFINED` means the host code (the Python script above
or, in the MPAS-coupled case, `mpas_musica.F`) supplies a runtime
multiplier on top of the YAML factor — this is what
`state.set_user_defined_rate_parameters(...)` does in the script. With an
initial concentration C₀ = 1 mol m⁻³ and both multipliers at 1.0, the
analytical reference equilibrium is AB ≈ 0.268 and A = B ≈ 0.732 mol m⁻³.
The standalone box reproduces those fractions at ~1 ppm by scaling the
reverse multiplier as described above. The coupled calculation retains both
multipliers at 1.0, but its cell-varying concentrations mean it has no single
domain-wide equilibrium fraction.

## 2.11 Standalone LNOx + O₃ box model

The standalone counterpart of §2.6, *minus* the lightning-NOx source
(which is a CheMPAS-A operator-split injection in
`mpas_lightning_nox.F`, not part of the MICM mechanism).
`scripts/musica_python/lnox_box.py` loads `micm_configs/lnox_o3.yaml`
into a single-cell MICM solver at mid-tropospheric conditions
(T = 240 K, P = 5×10⁴ Pa), seeds 0.2 ppb total NOx (50/50 NO/NO₂) and
50 ppb O₃, hardcodes `PHOTO.jNO2 = 0.01 s⁻¹`, and runs for 5 minutes
with 5-second output. That hardcoded rate has the same numeric value as
CheMPAS-A's no-TUV-x fallback `config_j_no2_max`; it is not the active TUV-x
rate or a cap on it in §2.6.

Pre-req: see Chapter 1's [Python environment for standalone
examples](01-overview.md) section.

Run:

```bash
cd "$CHEMPAS_ROOT"
python scripts/musica_python/lnox_box.py
```

The script writes `scripts/musica_python/lnox_box.nc` and
`scripts/musica_python/lnox_box.png`.

What to look for: NO and NO₂ partitioning settles within ~1 minute
to the Leighton ratio (jNO₂ / k_{NO+O₃}·[O₃]) — at the script's
conditions the simulated [NO]/[NO₂] reaches ~2.2, matching the
analytical expression. O₃ stays essentially constant: in this
simplified mechanism the back-reaction NO₂ + hν → NO + O₃ exactly
balances NO + O₃ → NO₂ + O₂ once PSS is reached, so there is no
net titration over the five-minute run. This is a direct independent check of
the analytical PSS computation referenced in Chapter 3 §3.8.
