# MPAS Chemistry Visualization

This document describes tools for visualizing MPAS-MUSICA chemistry output.
Verified scientific figures must also follow the versioned
[CheMPAS-A Scientific Plotting Protocol](PLOTTING_PROTOCOL.md), which defines
title hierarchy, UTC subtitles, quantity/comparison semantics, pressure-axis
orientation, scale selection, and provenance closure.

## Python Environment

A conda environment `mpas` provides the required packages:

```bash
# Create environment (if not already done)
conda create -n mpas python=3.11 numpy matplotlib netcdf4 -y

# Activate before running the examples below
conda activate mpas

# Set this from the CheMPAS-A source root
export CHEMPAS_ROOT="$(pwd)"
```

**Required packages:** numpy, matplotlib, netcdf4

## Scripts

All scripts are in the repository's `scripts/` directory. The examples call
them through `CHEMPAS_ROOT`, so run directories do not need script symlinks.

### plot_global_mvp.py

Create the verified Minimum Viable Product bundle from the passing M3
three-scenario attribution experiment. The plotter requires a passing report and all 27
retained histories. The catalog and plotter verify their byte sizes and
SHA-256 values before reading data, then produce seven 300-dpi PNG/vector-PDF
pairs under `chempas-science-plot-v1`.

```bash
export CHEMPAS_EMISSIONS_DATA_ROOT=/path/to/emissions-science
mvp_gate_commit=9f703f505051b8eb3700e9ecae927fc1c84746ca

python scripts/catalog_global_mvp_histories.py \
  --report "$CHEMPAS_EMISSIONS_DATA_ROOT/reports/global-mvp/$mvp_gate_commit/m3-report.json" \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --output docs/chempas/mvp/m3-history-manifest.json

python scripts/plot_global_mvp.py \
  --history-manifest docs/chempas/mvp/m3-history-manifest.json \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --outdir docs/chempas/mvp/figures \
  --manifest docs/chempas/mvp/figure-manifest.json \
  --dpi 300
```

Generation leaves visual inspection pending. Inspect every PNG for clipping,
labels, color scales, coastlines, and physical plausibility before recording
the attestation:

```bash
python scripts/plot_global_mvp.py \
  --attest-visual-inspection docs/chempas/mvp/figure-manifest.json
```

Figures 03 and 04 are true Daily Means of NO, NO2, CO, and O3 column burdens:
the plotter uses trapezoidal time integration across all nine instantaneous
history records from 2024-07-01 00:00 through 2024-07-02 00:00 UTC. Figure 02
is a model-step time-weighted Daily Mean source flux using all 192 left-endpoint
450-second samples, exactly matching MIEM source application. Figures 01, 05,
and 07 are explicitly Instantaneous. Figure 06 shows accumulated source mass
and endpoint closure rather than a mean.

The scenarios are **No Surface Emissions**, **Anthropogenic Emissions**, and
**Anthropogenic + Fire Emissions**.
The differences are **Anthropogenic Source Contribution** (Anthropogenic
Emissions minus No Surface Emissions) and **Fire Source Contribution**
(Anthropogenic + Fire Emissions minus Anthropogenic Emissions). No Surface
Emissions begins with the same nonzero chemical atmosphere as the other
scenarios; it is not a pristine or zero-burden reference.

The full scientific scope, interpretation limits, and evidence chain are in
[`MVP_PRE_RELEASE.md`](../mvp/MVP_PRE_RELEASE.md).

### plot_global_tropo_miem.py

Create the verified R3/F3 global tropospheric NOx bundle from passed,
same-provenance reports and four hash-verified final histories. The eight main
figure pairs establish the science narrative in protocol order:

1. final instantaneous NO/NO2 surface-emission fluxes;
2. reduced emissions-applied and emissions-applied-minus-withheld NO/NO2
   columns;
3. reduced hourly species burdens and family closure;
4. expanded emissions-continued and emissions-continued-minus-withheld NO/NO2
   columns;
5. expanded reactive-nitrogen evolution and closure;
6. expanded O3/HNO3/OH/HO2 column response;
7. vertical chemistry response; and
8. the supplemental resource comparison.

The independent concentration-audit script adds the ninth pair. Both scripts
use Title Case primary titles, subordinate UTC subtitles, lettered panels, and
explicit comparison/domain labels from the plotting protocol. Exact commands
and interpretation limits are in
[`GLOBAL_TROPOSPHERIC_NOX.md`](../musica/GLOBAL_TROPOSPHERIC_NOX.md#verified-figure-bundle).
The map panels are final-time snapshots, not daily means. R3 compares CAMS-NOx
emissions applied with emissions withheld during its analysis interval. F3
compares continuing with withholding emissions after a shared FS spin-up that
already used CAMS-NOx emissions; neither reference branch is a pristine
atmosphere.

### plot_global_miem_science.py

Create the Phase 9D global emissions, reactive-N budget, and diurnal-structure
bundle from the accepted A1 run. The plotter requires a passing A1 report,
verifies the exact tracked external-input manifest, resolves the retained run
through `CHEMPAS_EMISSIONS_DATA_ROOT`, and checks the full-file SHA-256 and byte
size of the final enabled and matched-control histories before reading them.
It uses all 25 accepted hourly report frames for time series and the final
hash-verified NetCDF frames for global source/response maps.

```bash
export CHEMPAS_EMISSIONS_DATA_ROOT=/path/to/emissions-science

python scripts/plot_global_miem_science.py \
  --report docs/chempas/musica/global-runs/stage9d-a1-report.json \
  --external-manifest \
    test_cases/global_miem/external-inputs.cams-glob-ant-v6.2-2024-07.json \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --outdir docs/chempas/musica/global-runs/figures \
  --manifest \
    docs/chempas/musica/global-runs/stage9d-figure-manifest.json \
  --prefix stage9d \
  --dpi 300
```

The outputs are:

- `stage9d_global_emissions_response.{png,pdf}`: explicit NO/NO2 surface flux
  and 24-hour enabled-minus-control column response;
- `stage9d_noy_budget.{png,pdf}`: hourly source rates, emitted-N/NOy closure,
  enabled/control partitioning, and retained-sector diagnostics; and
- `stage9d_diurnal_structure.{png,pdf}`: four TUV-x day/night cycles, global
  photolysis coverage, vertical NOy structure, and hemispheric evolution.

The script follows `scripts/style.py`, uses explicit units, rasterizes dense
map artists in the vector PDF, and refuses DPI below 300. The figure manifest
contains no workstation-absolute paths. It ties every image to the passing A1
report, external manifest, packaged inventory identity, final history hashes,
plot code/style hashes, executable, and dependency commits.

Scientific interpretation remains bounded: A1 proves coupled emissions,
dynamics, transport, reactive chemistry, photolysis, restart, and matched
control behavior. Although its meteorology is date matched, its Chapman-NOx
initial composition is idealized and not spun up, so first-day concentrations
are not production air-quality predictions.

The Phase 9E release rechecked the retained A1 inputs and all 47 assertions;
the result is canonically identical to the Stage 9D report after excluding the
expected free-disk telemetry field. The release manifest pins that comparison
and the figure-manifest SHA-256:
[`stage9e-release-manifest.json`](../musica/global-runs/stage9e-release-manifest.json).
The inspected PNG/PDF bundle is also copied to
`~/Desktop/CheMPAS-A-Phase9-global-emissions` for convenient review, but the
tracked figure and release manifests remain the authoritative identities.

### plot_miem_emissions.py

Create the verified MIEM NO/NO2 figure bundle from three complementary
eight-rank chem-box cases:

- R3 `cell_time_signature/exact_start` supplies the exact-grid horizontal
  signature and 9:1 NO:NO2 split;
- R6 `layered_diagnostics` supplies normalized elevated-source allocation and
  bounded total/sector/category closure; and
- an extended, emissions-only R2 `constant_flux` run supplies 30 minutes, 600
  chemistry intervals, and 31 output frames for cumulative source-to-tracer
  closure.

The plotter follows the repository protocol in `scripts/style.py`: NCAR colors,
fonts, and chemical labels; explicit physical units; final reference frames for
spatial and vertical panels; all frames for time histories; rasterized dense
fills; and both 300-dpi PNG and vector PDF output. It fails rather than plotting
unverified data if the MPAS grid IDs do not match the history, diagnostics are
missing or invalid, layered/group fields do not close, any R2/R3/R6 throughput
report did not pass, or a report's history SHA-256 does not match its supplied
file.

Reproduce the run inputs from a MUSICA-enabled `atmosphere_model`:

```bash
miem_plot_root="$(mktemp -d)"

scripts/test_miem_integration.sh \
  --scenario cell_time_signature \
  --variant exact_start \
  --executable ./atmosphere_model \
  --work-root "$miem_plot_root/r3" \
  --report-dir "$miem_plot_root/r3/reports" \
  --keep-success \
  --skip-mapping-test

scripts/test_miem_integration.sh \
  --scenario layered_diagnostics \
  --executable ./atmosphere_model \
  --work-root "$miem_plot_root/r6" \
  --report-dir "$miem_plot_root/r6/reports" \
  --keep-success \
  --skip-mapping-test

scripts/test_miem_integration.sh \
  --scenario constant_flux \
  --executable ./atmosphere_model \
  --override duration_seconds=1800 \
  --override output_interval_seconds=60 \
  --work-root "$miem_plot_root/r2_30min" \
  --report-dir "$miem_plot_root/r2_30min/reports" \
  --keep-success \
  --skip-mapping-test
```

Then create the figures and their SHA-256 manifest:

```bash
python scripts/plot_miem_emissions.py \
  --spatial-output "$miem_plot_root/r3/runs/R3-cell_time_signature-exact_start/output.nc" \
  --spatial-grid test_cases/chem_box/miem/assets/chem_box_grid.nc \
  --spatial-report "$miem_plot_root/r3/reports/R3-cell_time_signature-exact_start.json" \
  --layered-output "$miem_plot_root/r6/runs/R6-layered_diagnostics-default/output.nc" \
  --layered-report "$miem_plot_root/r6/reports/R6-layered_diagnostics-default.json" \
  --budget-output "$miem_plot_root/r2_30min/runs/R2-constant_flux-default/output.nc" \
  --budget-report "$miem_plot_root/r2_30min/reports/R2-constant_flux-default.json" \
  --outdir docs/_static \
  --prefix miem_emissions \
  --manifest docs/chempas/results/miem-emissions-figure-manifest.json
```

The tracked plots use synthetic inventories generated deterministically inside
the retained temporary runs. Those inventories and the NetCDF model histories
are evidence inputs, not scientific emissions products, and are not committed.
The canonical mesh is the tracked external grid input; a production plot must
instead use a scientifically sourced inventory already conservatively remapped
to its exact production mesh.

The 30-minute R2 extension is the right longer run for the current verification
question: it exercises 600 chemistry transactions and makes cumulative drift
visible while retaining an analytically isolated budget. Extending R3 or R6
does not add a new contract because their deterministic spatial and layer/group
signatures are established in the first applied interval. The next longer run
should therefore wait for a science-grade exact-grid inventory: first use a
one-hour production-grid throughput shakedown, then use at least a full diurnal
cycle when the goal is temporal interpolation plus transport and chemistry.
Such a run must define its own scientific budget expectations; direct NO/NO2
tracer equality is no longer valid once reactions, transport losses, or other
sources are active.

### plot_chemistry.py

Visualize chemistry tracer output (currently `qA`, `qB`, `qAB` for ABBA tests).

**Basic usage:**
```bash
cd ~/Data/CheMPAS/supercell
python "$CHEMPAS_ROOT/scripts/plot_chemistry.py" -o chemistry.png
```

**Options:**

| Option | Description |
|--------|-------------|
| `-i, --input` | Input file (default: output.nc) |
| `-o, --output` | Output figure filename |
| `-l, --level` | Vertical level for slices (default: 10) |
| `-t, --time` | Time index (default: -1 = last) |
| `--time-series` | Generate spatial maps at multiple times |
| `--diff` | Generate difference plots (t - t0) |
| `--diff-consecutive` | Generate consecutive diffs (t - t-1) |
| `--n-times` | Number of time steps for series (default: 6) |
| `--show` | Display plot interactively |

**Examples:**

```bash
# Quick summary plot
python "$CHEMPAS_ROOT/scripts/plot_chemistry.py" -o quick.png

# Spatial time evolution (6 panels showing pattern evolution)
python "$CHEMPAS_ROOT/scripts/plot_chemistry.py" -o advection.png --time-series

# Difference from initial (reveals advection + chemistry)
python "$CHEMPAS_ROOT/scripts/plot_chemistry.py" -o advection.png --diff

# Consecutive differences (instantaneous changes)
python "$CHEMPAS_ROOT/scripts/plot_chemistry.py" -o advection.png --diff-consecutive

# Specific level and time
python "$CHEMPAS_ROOT/scripts/plot_chemistry.py" -o level20.png --level 20 --time 5

# More time panels
python "$CHEMPAS_ROOT/scripts/plot_chemistry.py" -o detailed.png --time-series --n-times 9
```

**Output figures:**

| Suffix | Content |
|--------|---------|
| `.png` | Main 3x3 summary (horizontal slices, vertical cross-sections, time evolution) |
| `_timeseries.png` | Spatial maps at multiple times |
| `_diff.png` | Difference from initial conditions |
| `_diff_consecutive.png` | Consecutive time differences |

### init_tracer_sine.py

Initialize tracers with sine wave patterns for advection studies.

**Basic usage:**
```bash
python "$CHEMPAS_ROOT/scripts/init_tracer_sine.py" \
  -i supercell_init.nc -t qAB --waves-x 2 --amplitude 0.4 --offset 0.6
```

**Options:**

| Option | Description |
|--------|-------------|
| `-i, --input` | Input init file (default: supercell_init.nc) |
| `-o, --output` | Output file (default: edit in place) |
| `-t, --tracer` | Tracer variable name (default: qAB) |
| `--amplitude` | Sine wave amplitude (default: 0.5) |
| `--offset` | Baseline value (default: 1.0) |
| `--waves-x` | Number of waves in x direction (default: 1) |
| `--waves-y` | Number of waves in y direction (default: 1) |

**Examples:**

```bash
# 2x2 wave pattern, values 0.2 to 1.0
python "$CHEMPAS_ROOT/scripts/init_tracer_sine.py" \
  -t qAB --waves-x 2 --waves-y 2 --amplitude 0.4 --offset 0.6

# Single wave in x only
python "$CHEMPAS_ROOT/scripts/init_tracer_sine.py" \
  -t qAB --waves-x 1 --waves-y 0 --amplitude 0.5 --offset 0.5

# Save to new file instead of editing in place
python "$CHEMPAS_ROOT/scripts/init_tracer_sine.py" \
  -i supercell_init.nc -o supercell_init_sine.nc -t qAB
```

## Workflows

### Quick Look

After a run, generate a quick summary:

```bash
cd ~/Data/CheMPAS/supercell
python "$CHEMPAS_ROOT/scripts/plot_chemistry.py" -o quick.png
open quick.png
```

### Advection Study

1. **Set up initial conditions with gradients:**
   ```bash
   cp supercell_init.nc supercell_init_uniform.nc  # Backup
   python "$CHEMPAS_ROOT/scripts/init_tracer_sine.py" \
     -t qAB --waves-x 2 --amplitude 0.4 --offset 0.6
   ```

2. **Configure longer run** (edit `namelist.atmosphere`):
   ```
   config_run_duration = '00:15:00'
   ```

3. **Adjust output interval** (edit `streams.atmosphere`):
   ```xml
   output_interval="00:00:30"
   ```

4. **Run the model:**
   ```bash
   mpiexec -n 8 "$CHEMPAS_ROOT/atmosphere_model"
   ```

5. **Generate all visualizations:**
   ```bash
   python "$CHEMPAS_ROOT/scripts/plot_chemistry.py" \
     -o advection.png --time-series --diff
   open advection.png advection_timeseries.png advection_diff.png
   ```

### Interpreting Results

**Time series plots:**
- Show spatial pattern evolution
- Chemistry decay: overall values decrease as AB → A + B
- Advection: pattern distortion/displacement

**Difference plots (t - t0):**
- Blue: tracer decreased (chemistry decay)
- Red: tracer increased (advection brought higher values)
- Symmetric pattern: chemistry-dominated
- Asymmetric pattern: advection effects visible

**Consecutive diffs (t - t-1):**
- Show instantaneous rate of change
- Useful for seeing where chemistry is most active
- Large values at concentration peaks (more reactant available)

## Technical Notes

### Unstructured Mesh Handling

The scripts use matplotlib's `Triangulation` to visualize the MPAS unstructured mesh:

```python
from matplotlib.tri import Triangulation
tri = Triangulation(xCell, yCell)  # Delaunay triangulation
ax.tricontourf(tri, values, ...)
```

**Limitations:**
- Uses Delaunay triangulation of cell centers (not actual MPAS Voronoi topology)
- May have minor artifacts at domain edges
- Future: consider uxarray for proper mesh handling if visualization artifacts
  near mesh boundaries become important.

### Output Variables

Chemistry tracers in `output.nc` for the ABBA test mechanism:

| Variable | Description | Units |
|----------|-------------|-------|
| `qAB` | Molecular AB mixing ratio | kg/kg |
| `qA` | Atomic A mixing ratio | kg/kg |
| `qB` | Atomic B mixing ratio | kg/kg |

Wind fields for understanding advection:

| Variable | Description |
|----------|-------------|
| `uReconstructZonal` | Zonal (east-west) wind at cell centers |
| `uReconstructMeridional` | Meridional (north-south) wind at cell centers |
| `w` | Vertical velocity |
