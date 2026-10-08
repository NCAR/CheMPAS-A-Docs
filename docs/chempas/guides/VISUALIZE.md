# MPAS Chemistry Visualization

This document describes tools for visualizing MPAS-MUSICA chemistry output.
Worked examples for the public release are on the
[CheMPAS-A wiki](https://github.com/NCAR/CheMPAS-A/wiki/Examples).

## Python Environment

A conda environment `mpas` provides the required packages:

```bash
# Create environment (if not already done)
conda create -n mpas python=3.11 numpy matplotlib netcdf4 pyyaml -y

# Activate before running the examples below
conda activate mpas

# Set this from the CheMPAS-A source root
export CHEMPAS_ROOT="$(pwd)"
```

**Required packages:** numpy, matplotlib, netcdf4, pyyaml

## Scripts

The scripts are in the `scripts/` directory of the CheMPAS-A development
repository. Of the scripts described here, the public release includes only
`init_tracer_sine.py`; the plotting scripts are not part of it.

Run the global and MIEM plotters from the source root. They share the NCAR
colors, fonts, and chemical labels in `scripts/style.py` and write each figure
as a 300-dpi PNG and a vector PDF. The global plotters refuse a `--dpi` below
300. Except for `plot_global_mvp.py`, they also accept `--context` with
`default`, `publication`, or `presentation` to select font sizes. The other
examples call scripts through `CHEMPAS_ROOT`, so run directories do not need
script symlinks.

### plot_global_mvp.py

Plot the global chemistry and emissions MVP experiment, which runs three
scenarios over the same UTC day. `catalog_global_mvp_histories.py` reads the
experiment's passing run report and lists its 27 history files (nine per
scenario) and its input files by path relative to the data root.
`plot_global_mvp.py` reads that list and writes seven PNG/PDF pairs. The
report, run directories, and inputs must be below `--data-root`; the figure
directory and the `--manifest` file that lists the figures must be inside the
source tree.

```bash
export CHEMPAS_EMISSIONS_DATA_ROOT=/path/to/emissions-science

python scripts/catalog_global_mvp_histories.py \
  --report "$CHEMPAS_EMISSIONS_DATA_ROOT/path/to/report.json" \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --output global-emissions-plots/history-manifest.json

python scripts/plot_global_mvp.py \
  --history-manifest global-emissions-plots/history-manifest.json \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --outdir global-emissions-plots/figures \
  --manifest global-emissions-plots/figure-manifest.json \
  --dpi 300
```

The figures are:

1. `01_upper_o3_climatology`: prescribed upper-atmosphere O3 climatology;
2. `02_surface_source_fluxes`: CAMS and FINN surface source fluxes;
3. `03_daily_mean_absolute_columns`: Daily Mean NO, NO2, CO, and O3 column
   burdens;
4. `04_daily_mean_column_contributions`: Daily Mean anthropogenic and fire
   column contributions;
5. `05_diurnal_photolysis`: diurnal TUV-x photolysis structure;
6. `06_source_mass_and_closure`: applied source mass histories and closure;
   and
7. `07_model_top_o3_stitch`: model-top O3 profile stitch.

Figures 03 and 04 are true Daily Means of NO, NO2, CO, and O3 column burdens:
the plotter uses trapezoidal time integration across all nine instantaneous
history records from 2024-07-01 00:00 through 2024-07-02 00:00 UTC. Figure 02
is a model-step time-weighted Daily Mean source flux using all 192 left-endpoint
450-second samples, exactly matching MIEM source application. Figures 01, 05,
and 07 are Instantaneous. Figure 06 shows accumulated source mass and endpoint
closure rather than a mean.

The scenarios are **No Surface Emissions**, **Anthropogenic Emissions**, and
**Anthropogenic + Fire Emissions**.
The differences are **Anthropogenic Source Contribution** (Anthropogenic
Emissions minus No Surface Emissions) and **Fire Source Contribution**
(Anthropogenic + Fire Emissions minus Anthropogenic Emissions). No Surface
Emissions begins with the same nonzero chemical atmosphere as the other
scenarios; it is not a pristine or zero-burden reference.

The scientific scope and interpretation limits of the experiment are on the
wiki page
[Global Chemistry and Emissions](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions).

### plot_global_tropo_miem.py

Plot two one-day global tropospheric NOx runs that apply the CAMS-GLOB-ANT v6.2
NO and NO2 inventory with lightning NOx off. The reduced run uses the
NO-NO2-O3 mechanism in `micm_configs/global_cams_lnox_o3.yaml` with `jNO2`
photolysis. The expanded run uses the Ox-HOx-NOx-CO-CH4 mechanism with HNO3 in
`micm_configs/global_cams_tropo_ch4nox.yaml` with eight TUV-x rates. Each run
has an emissions branch and a branch that withholds emissions over the same
interval. The plotter reads the passing report of each run, finds the final
history of each branch below the matching run root, and writes eight PNG/PDF
pairs:

1. `global_tropo_surface_emissions`: final instantaneous NO/NO2
   surface-emission fluxes;
2. `global_tropo_reduced_nox_columns`: reduced emissions-applied and
   emissions-applied-minus-withheld NO/NO2 columns;
3. `global_tropo_reduced_budget`: reduced hourly species burdens and family
   closure;
4. `global_tropo_expanded_nox_columns`: expanded emissions-continued and
   emissions-continued-minus-withheld NO/NO2 columns;
5. `global_tropo_expanded_partition`: expanded reactive-nitrogen evolution and
   closure;
6. `global_tropo_expanded_response`: expanded O3/HNO3/OH/HO2 column response;
7. `global_tropo_vertical_response`: vertical chemistry response; and
8. `global_tropo_resource_comparison`: reduced/expanded resource comparison.

```bash
python scripts/plot_global_tropo_miem.py \
  --reduced-report /path/to/reduced-report.json \
  --expanded-report /path/to/expanded-report.json \
  --reduced-run-root /path/to/reduced-runs \
  --expanded-run-root /path/to/expanded-runs \
  --outdir global-tropo-figures \
  --manifest global-tropo-figures/figure-manifest.json \
  --dpi 300 --context publication
```

The map panels are final-time snapshots, not daily means. In the reduced run,
differences are CAMS-NOx emissions applied minus emissions withheld during the
analysis interval. The expanded run starts from a shared one-day spin-up that
already applied CAMS-NOx emissions, so its differences are emissions continued
minus emissions withheld; neither reference branch is a pristine atmosphere.

`audit_global_tropo_concentrations.py` takes the same reports and run roots and
screens the same final histories for physically plausible concentrations. It
converts mass mixing ratio to dry-air molar mixing ratio, converts O, O1D, OH,
HO2, and CH3O2 to number density, and reports extrema and weighted statistics
for pressures of at least 500 hPa, 150–500 hPa, the full at-least-150 hPa
diagnostic domain, and the column above it. `--audit` names the JSON result and
`--figure-stem` the PNG/PDF pair:

```bash
python scripts/audit_global_tropo_concentrations.py \
  --reduced-report /path/to/reduced-report.json \
  --expanded-report /path/to/expanded-report.json \
  --reduced-run-root /path/to/reduced-runs \
  --expanded-run-root /path/to/expanded-runs \
  --audit global-tropo-figures/concentration-audit.json \
  --figure-stem global-tropo-figures/global_tropo_concentration_ranges \
  --dpi 300 --context publication
```

The audit is a physical-plausibility screen, not an observational skill score.

### plot_global_miem_science.py

Plot a one-day global run with Chapman-NOx chemistry, TUV-x photolysis, and the
CAMS-GLOB-ANT v6.2 NO/NO2 inventory, together with its matched control run
without emissions. The plotter takes the run's passing throughput report, the
tracked external-input manifest that describes the inventory, and the data root
below which the report's history paths resolve. Time series use the report's
25 hourly frames; global source and response maps use the final emissions and
control histories.

```bash
export CHEMPAS_EMISSIONS_DATA_ROOT=/path/to/emissions-science

python scripts/plot_global_miem_science.py \
  --report /path/to/throughput-report.json \
  --external-manifest \
    test_cases/global_miem/external-inputs.cams-glob-ant-v6.2-2024-07.json \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --outdir global-miem-figures \
  --manifest global-miem-figures/figure-manifest.json \
  --prefix chapman_nox \
  --dpi 300
```

`--prefix` sets the start of each output file name:

- `<prefix>_global_emissions_response.{png,pdf}`: explicit NO/NO2 surface flux
  and 24-hour enabled-minus-control column response;
- `<prefix>_noy_budget.{png,pdf}`: hourly source rates, emitted-N/NOy closure,
  enabled/control partitioning, and retained-sector diagnostics; and
- `<prefix>_diurnal_structure.{png,pdf}`: four TUV-x day/night cycles, global
  photolysis coverage, vertical NOy structure, and hemispheric evolution.

Dense map artists are rasterized in the vector PDF. The run uses date-matched
meteorology, but its Chapman-NOx initial composition is idealized and not spun
up, so first-day concentrations are not air-quality predictions.

### plot_miem_emissions.py

Plot MIEM NO/NO2 emissions from three eight-rank chem-box cases run by
`scripts/test_miem_integration.sh`:

- `cell_time_signature`, variant `exact_start`, supplies the exact-grid
  horizontal signature and 9:1 NO:NO2 split;
- `layered_diagnostics` supplies normalized elevated-source allocation and
  bounded total/sector/category closure; and
- `constant_flux`, extended to an emissions-only 30-minute run, supplies 600
  chemistry intervals and 31 output frames for cumulative source-to-tracer
  closure.

The plotter writes three PNG/PDF pairs: `miem_emissions_spatial.png` shows the
final-frame NO and NO2 surface fluxes, `miem_emissions_vertical.png` the
elevated-source allocation and sector/category closure, and
`miem_emissions_budget.png` the applied source rate and cumulative emitted mass
against tracer mass over all frames. Spatial and vertical panels use the final
frame; time histories use every frame. Dense fills are rasterized in the PDF.
The plotter stops without plotting if the MPAS grid IDs do not match the
history, diagnostics are missing or invalid, layered or group fields do not
close, or any of the three run reports did not pass.

Produce the runs from a MUSICA-enabled `atmosphere_model`. `--keep-success`
keeps each run directory after the run passes:

```bash
miem_plot_root="$(mktemp -d)"

scripts/test_miem_integration.sh \
  --scenario cell_time_signature \
  --variant exact_start \
  --executable ./atmosphere_model \
  --work-root "$miem_plot_root/spatial" \
  --report-dir "$miem_plot_root/spatial/reports" \
  --keep-success \
  --skip-mapping-test

scripts/test_miem_integration.sh \
  --scenario layered_diagnostics \
  --executable ./atmosphere_model \
  --work-root "$miem_plot_root/layered" \
  --report-dir "$miem_plot_root/layered/reports" \
  --keep-success \
  --skip-mapping-test

scripts/test_miem_integration.sh \
  --scenario constant_flux \
  --executable ./atmosphere_model \
  --override duration_seconds=1800 \
  --override output_interval_seconds=60 \
  --work-root "$miem_plot_root/budget" \
  --report-dir "$miem_plot_root/budget/reports" \
  --keep-success \
  --skip-mapping-test
```

Each command writes `runs/<id>-<scenario>-<variant>/output.nc` below its work
root and `<id>-<scenario>-<variant>.json` in its report directory; the variant
is `default` for scenarios without named variants. Then create the figures:

```bash
python scripts/plot_miem_emissions.py \
  --spatial-output "$miem_plot_root"/spatial/runs/*-cell_time_signature-exact_start/output.nc \
  --spatial-grid test_cases/chem_box/miem/assets/chem_box_grid.nc \
  --spatial-report "$miem_plot_root"/spatial/reports/*-cell_time_signature-exact_start.json \
  --layered-output "$miem_plot_root"/layered/runs/*-layered_diagnostics-default/output.nc \
  --layered-report "$miem_plot_root"/layered/reports/*-layered_diagnostics-default.json \
  --budget-output "$miem_plot_root"/budget/runs/*-constant_flux-default/output.nc \
  --budget-report "$miem_plot_root"/budget/reports/*-constant_flux-default.json \
  --outdir "$miem_plot_root/figures" \
  --prefix miem_emissions
```

The plotted inventories are synthetic, generated deterministically inside the
temporary runs; they exercise the coupling and are not scientific emissions
products. The canonical mesh is the tracked external grid input. A production
plot must instead use a scientifically sourced inventory already conservatively
remapped to its exact production mesh.

The 30-minute `constant_flux` run exercises 600 chemistry intervals and makes
cumulative drift visible while keeping an analytically isolated budget. Longer
`cell_time_signature` or `layered_diagnostics` runs show nothing new, because
their spatial and layer/group signatures are established in the first applied
interval. A longer emissions run needs a science-grade exact-grid inventory and
its own scientific budget expectations; direct NO/NO2 tracer equality is no
longer valid once reactions, transport losses, or other sources are active.

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

`plot_chemistry.py` and `plot_miem_emissions.py` use matplotlib's
`Triangulation` to visualize the MPAS unstructured mesh:

```python
from matplotlib.tri import Triangulation
tri = Triangulation(xCell, yCell)  # Delaunay triangulation
ax.tricontourf(tri, values, ...)
```

**Limitations:**
- Uses Delaunay triangulation of cell centers (not actual MPAS Voronoi topology)
- May have minor artifacts at domain edges
- Where artifacts near mesh boundaries matter, consider uxarray, which reads
  the MPAS mesh topology directly.

The global plotters instead draw one rasterized marker per cell center in
longitude-latitude coordinates.

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
