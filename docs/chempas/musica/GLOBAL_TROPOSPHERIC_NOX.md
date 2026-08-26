# Global tropospheric NOx emissions ladder

This is the reproducible x1.40962 workflow for applying the accepted explicit
CAMS-GLOB-ANT v6.2 NO and NO2 inventory with tropospheric chemistry. It is a
new evidence namespace; it does not replace the accepted Phase 9 Chapman-NOx
reports.

The implementation deliberately has two tiers. The reduced tier is the
LNOx-derived NO-NO2-O3 cycle and is the primary global source/coupling test.
The expanded tier adds Ox-HOx-NOx-CO-CH4 chemistry and HNO3 after an independent
chemical-kernel qualification. Lightning NOx is exactly zero throughout, so
MIEM is the only NOx source.

## Scientific boundary

| Tier | MICM mechanism | Photolysis | Valid interpretation |
|---|---|---|---|
| Reduced | `global_cams_lnox_o3.yaml` | `jNO2` | NOx/Ox source-response, Leighton cycling, ozone titration, transport, and restart behavior |
| Expanded | `global_cams_tropo_ch4nox.yaml` | Eight TUV-x rates | Experimental radical-mediated Ox/NOy response and NO/NO2/HNO3 partitioning |

Both mechanisms expose exactly `EMIS.NO` and `EMIS.NO2`, preserving the
inventory's accepted explicit speciation. The reduced mechanism conserves NOx
and Ox apart from those sources. The expanded mechanism uses MICM's native
Troe form for `OH + NO2 (+M) -> HNO3`; the parser/runtime test compares a
16-point temperature-pressure matrix with the independent expression from the
[NASA/JPL kinetics evaluation](https://science.jpl.nasa.gov/projects/data-evaluation/).

This is not a production air-quality mechanism. In particular, it lacks dry
and wet deposition, detailed anthropogenic and biogenic VOC chemistry,
nighttime NO3/N2O5 chemistry, soil/fire/biogenic emissions, online plume rise,
chemical data assimilation, and a multiweek chemical spin-up. The one-day FS
spin-up conditions fast radicals and diurnal partitioning only. Chemistry is
solved at all 26 model levels; the fixed 150 hPa mask is diagnostic and does
not turn chemistry off above it. Above-mask results are stability diagnostics,
not stratospheric chemistry.

## Frozen inputs and generated state

Large inputs and model outputs stay below `CHEMPAS_EMISSIONS_DATA_ROOT`. The
tracked base manifest and global-tropospheric overlay pin the date-matched GFS
state, x1.40962 mesh/partition, science inventory, and the two derived
chemistry states by logical path, size, and SHA-256.

The initializer copies the GFS state and appends only the declared chemistry
tracers. It proves that all existing arrays, global attributes, the clock, and
host `qv` remain bitwise unchanged. Expanded H2O is read-only and host-bound to
`qv`; third-body `M` is derived by MICM. Neither `qH2O` nor `qM` is created.
The deterministic backgrounds are suitable for qualification, but are not an
assimilated chemical analysis.

To reproduce the derived states in a scratch location, then compare their
reported hashes with the tracked overlay:

```bash
export CHEMPAS_EMISSIONS_DATA_ROOT=/path/to/emissions-science
base="$CHEMPAS_EMISSIONS_DATA_ROOT/initial_conditions/noaa-gfs-20240701T00Z/x1.40962.gfs-20240701T00Z.init.nc"
scratch="$CHEMPAS_EMISSIONS_DATA_ROOT/rebuild/global-tropo-init"
mkdir -p "$scratch"

python scripts/prepare_global_tropo_initial_condition.py \
  --input "$base" \
  --output "$scratch/x1.40962.gfs-20240701T00Z.reduced-tropo.init.nc" \
  --mechanism reduced \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --report "$scratch/reduced-audit.json"

python scripts/prepare_global_tropo_initial_condition.py \
  --input "$base" \
  --output "$scratch/x1.40962.gfs-20240701T00Z.expanded-tropo.init.nc" \
  --mechanism expanded \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --report "$scratch/expanded-audit.json"
```

The canonical reduced and expanded files currently pinned by the overlay have
SHA-256 values `ebbb698e...50fe` and `7ccb0670...e78`, respectively. Use the
complete values in `external-inputs.overlay.json`; abbreviated values are for
human orientation only.

## Preflight and chemical qualification

Use a Python environment containing NumPy, netCDF4, PyYAML, and Matplotlib.
The tested MPAS environment is shown here explicitly:

```bash
conda activate mpas
MPAS_PYTHON="$CONDA_PREFIX/bin/python"

"$MPAS_PYTHON" -m unittest \
  tests.test_global_tropo_mechanisms \
  tests.test_prepare_global_tropo_initial_condition \
  tests.test_global_tropo_miem_harness \
  tests.test_global_tropo_concentrations

scripts/test_global_tropo_troe.sh
scripts/test_musica_emission_contracts.sh
```

F0 compiles against the pinned installed C++ MUSICA/MICM stack. It qualifies
five boxes, a three-level 24-hour column, all eight photolysis parameters,
radical day/night behavior, high-NOx HNO3 formation, elemental-N conservation,
and the 16-point Troe matrix:

```bash
commit="$(git rev-parse HEAD)"
export CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT="${CHEMPAS_EMISSIONS_DATA_ROOT}/reports/global-tropo/${commit}"
mkdir -p "$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT"

"$MPAS_PYTHON" scripts/run_global_tropo_f0.py \
  --report "$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT/f0-report.json"
```

F0 may be run early for development, but it becomes a promotion receipt only
when its report says both `overall_pass: true` and `promotable: true`.

## Same-commit promotion discipline

Run the complete ladder from one clean tracked-and-untracked worktree and one
unchanged `atmosphere_model`. Intermediate receipts remain outside Git under a
directory keyed by the full CheMPAS commit. This is essential: committing each
receipt between gates would change the source revision and invalidate the
R3/F3 comparison.

The runner refuses a later gate unless the preceding receipt is passed,
promotable, from the current commit, and—except for F0—from the identical
atmosphere executable. `--allow-dirty` exists only for non-promotable
development runs and cannot unlock the next gate.

Check resource forecasts without MPI or promotion requirements first:

```bash
"$MPAS_PYTHON" scripts/run_global_tropo_miem_integration.py \
  --gate R3 --stage-only \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --promotion-root "$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT" \
  --executable ./atmosphere_model

"$MPAS_PYTHON" scripts/run_global_tropo_miem_integration.py \
  --gate FS --stage-only \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --promotion-root "$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT" \
  --executable ./atmosphere_model
```

Each stage report records predicted history/restart volume, reserve, MPI rank
count, executable hash, external inputs, TUV-x data-tree hash, and all planned
variant directories.

## Gate ladder

| Gate | Duration | Variants | Decisive evidence |
|---|---:|---|---|
| R0 | 5 min | MIEM off, exact-zero MIEM | bitwise zero-source identity; NOx/Ox closure |
| R-CAL | 15 min | strict, candidate | solver tolerance calibration |
| R1 | 1 h | emissions applied, emissions withheld | science source/response and full sector closure |
| R2 | 6 h | continuous, 3+3 h, emissions withheld | restart and paired-branch response |
| R3 | 24 h | continuous, 12+12 h, emissions withheld | complete diurnal reduced acceptance |
| F0 | boxes + 24 h column | C++ kernel | expanded chemistry/rate qualification |
| F-CAL | 15 min | strict, candidate | expanded solver calibration |
| F1 | 1 h | emissions applied, emissions withheld | eight-rate global shakedown and NOy response |
| FS | 24 h | CAMS-NOx emissions applied | common radical/partition spin-up and boundary restart |
| F2 | 6 h | continuous, 3+3 h, emissions withheld after FS | restart from immutable FS boundary |
| F3 | 24 h | continuous, 12+12 h, emissions withheld after FS | expanded diurnal experiment and resources |

The report identifier `no_miem_control` is retained for schema compatibility,
but it does not denote a pristine or never-emitted atmosphere. R3 starts from a
nonzero atmospheric NOx state and withholds CAMS-NOx emissions only during the
analysis interval. Every F2/F3 branch starts from the same FS restart produced
with CAMS-NOx emissions; the paired branch then withholds additional emissions
during its analysis interval.

Run reduced gates in order:

```bash
for gate in R0 R-CAL R1 R2 R3; do
  "$MPAS_PYTHON" scripts/run_global_tropo_miem_integration.py \
    --gate "$gate" \
    --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
    --promotion-root "$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT" \
    --executable ./atmosphere_model \
    --mpi-launcher mpiexec || exit
done
```

After the F0 command above has produced a promotable receipt, run the first
expanded gates:

```bash
for gate in F-CAL F1 FS; do
  "$MPAS_PYTHON" scripts/run_global_tropo_miem_integration.py \
    --gate "$gate" \
    --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
    --promotion-root "$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT" \
    --executable ./atmosphere_model \
    --mpi-launcher mpiexec || exit
done
```

Every model gate writes a closed JSON report. The checker independently
reconstructs inventory samples, integrated source, mechanism-aware NOx/Ox/NOy
budgets, restart/paired-branch differences, photolysis, radical cycles, vertical and
hemispheric partitions, host-water binding, clipping/log health, resource use,
and provenance. History records are gate-root-relative and hash-verified.

## Immutable FS restart handoff

F2 and F3 may use only the restart recorded by the passed FS report at
`2024-07-02_00:00:00`. Register it once into external storage and an external
runtime overlay; do not edit the tracked base overlay during the ladder:

```bash
fs_report="$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT/fs-report.json"
fs_root="$(jq -r '.inputs.output_path_contract.gate_run_root' "$fs_report")"
fs_restart="$(jq -r '.runs.continuous.output.restart_files[0].path' "$fs_report")"
runtime_overlay="$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT/external-inputs.spinup.overlay.json"

"$MPAS_PYTHON" scripts/register_global_tropo_spinup_restart.py \
  --fs-report "$fs_report" \
  --restart "$fs_root/$fs_restart" \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --registration "$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT/fs-restart-registration.json" \
  --overlay "$runtime_overlay" \
  --update-overlay
```

Registration verifies the exact boundary time, global cell IDs, all expanded
chemistry tracers, host `qv`, absence of `qH2O`/`qM`, mechanism and executable
hashes, and the FS report's restart size/hash. It copies atomically and refuses
a conflicting target or overlay record.

Run the remaining gates with that runtime overlay:

```bash
for gate in F2 F3; do
  "$MPAS_PYTHON" scripts/run_global_tropo_miem_integration.py \
    --gate "$gate" \
    --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
    --promotion-root "$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT" \
    --external-overlay "$runtime_overlay" \
    --executable ./atmosphere_model \
    --mpi-launcher mpiexec || exit
done
```

## Portable compact evidence

After every gate and the FS restart registration pass, publish portable review
copies of the eleven reports, registration, and runtime overlay. The publisher
revalidates every receipt, requires a single commit/executable, records each
source receipt hash and its own generator hash, and refuses any private absolute
path left after replacing the declared repository, data, MUSICA, and ephemeral
F0 prefixes:

```bash
source_repo_root="$(git rev-parse --show-toplevel)"
musica_prefix="$(jq -r '.software.musica_prefix' \
  "$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT/f0-report.json")"

"$MPAS_PYTHON" scripts/publish_global_tropo_evidence.py \
  --promotion-root "$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT" \
  --outdir docs/chempas/musica/global-tropo-runs \
  --source-repo-root "$source_repo_root" \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --musica-prefix "$musica_prefix"
```

## Verified figure bundle

The plotter accepts only passed/promotable R3 and F3 reports with the same
commit, executable, and science inventory and with lightning disabled. It
resolves each selected final history below an explicit gate root, verifies its
size and SHA-256, and refuses mixed or failed evidence.

```bash
r3_source="$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT/r3-report.json"
f3_source="$CHEMPAS_GLOBAL_TROPO_PROMOTION_ROOT/f3-report.json"
r3_root="$(jq -r '.inputs.output_path_contract.gate_run_root' "$r3_source")"
f3_root="$(jq -r '.inputs.output_path_contract.gate_run_root' "$f3_source")"
r3_report=docs/chempas/musica/global-tropo-runs/r3-report.json
f3_report=docs/chempas/musica/global-tropo-runs/f3-report.json

"$MPAS_PYTHON" scripts/plot_global_tropo_miem.py \
  --reduced-report "$r3_report" \
  --expanded-report "$f3_report" \
  --reduced-run-root "$r3_root" \
  --expanded-run-root "$f3_root" \
  --outdir docs/chempas/musica/global-tropo-runs/figures \
  --manifest docs/chempas/musica/global-tropo-runs/figure-manifest.json \
  --dpi 300 --context publication
```

The eight PNG/PDF pairs cover final instantaneous surface NO/NO2 emission
fluxes; emissions-branch and emissions-minus-withheld NO/NO2
diagnostic-tropospheric columns for both R3 and F3; reduced NO/NO2 burden
evolution and NOx/Ox closure; expanded
NO/NO2/HNO3 partition and NOy closure; expanded O3/HNO3/OH/HO2 column
response; vertical response with the 150 hPa diagnostic boundary; and
reduced/expanded resources. Together with the concentration-audit pair, the
review bundle contains nine raster/vector figure pairs.

The map and concentration panels are instantaneous states at their stated
valid times, not daily means. Hourly burden panels are trajectories, and
family-source curves are cumulative over the stated interval. In R3,
differences mean CAMS-NOx emissions applied minus emissions withheld during
analysis. In F3, they mean emissions continued minus emissions withheld during
analysis after the shared FS spin-up with CAMS-NOx emissions. They diagnose the
marginal effect of continuing the emissions, not an emitting atmosphere versus
a pristine atmosphere.

All figures follow
[`chempas-science-plot-v1`](../guides/PLOTTING_PROTOCOL.md): Title Case figure
titles, UTC date or valid-time subtitles, lettered sentence-case panels,
explicit vertical domains and physical emissions/reference semantics, and
pressure decreasing upward. The closed manifest records the protocol version
and hashes both reports, all four selected NetCDF histories, the protocol, plot
script/style/schema, and every rendered file.

## Physical concentration audit

Run the independent range audit from the same passed/promotable R3 and F3
reports and hash-verified final histories:

```bash
"$MPAS_PYTHON" scripts/audit_global_tropo_concentrations.py \
  --reduced-report "$r3_report" \
  --expanded-report "$f3_report" \
  --reduced-run-root "$r3_root" \
  --expanded-run-root "$f3_root" \
  --audit docs/chempas/musica/global-tropo-runs/concentration-audit.json \
  --figure-stem docs/chempas/musica/global-tropo-runs/figures/global_tropo_concentration_ranges \
  --dpi 300 --context publication
```

This audit converts mass mixing ratio to dry-air molar mixing ratio, converts
O/O1D/OH/HO2/CH3O2 to molecule number density using the model density, and
reports exact extrema plus air-mass- or volume-weighted statistics in four
pressure bands: at least 500 hPa, 150--500 hPa, the complete at-least-150 hPa
diagnostic domain, and the unqualified column above it. Hard bounds exclude
nonphysical dry-air pressure/density, global mesh area or atmospheric mass,
negative state, major-species drift, and numerical blow-up in the complete
column. The integrated dry-air mass is also converted to a mean
hydrostatic-equivalent pressure as an independent check on the volume and
air-mass weights. Separate screening envelopes are deliberately much broader
than their observational anchors: NOAA's 2024 global CH4 abundance, published
global OH model ranges, observation-calibrated global O3, NASA aircraft NOx,
and aircraft peroxide measurements. Passing is a physical-plausibility screen,
not an observational skill score or a claim that one day has produced a
chemical climatology.

Only after the entire ladder and figures pass should the compact reports,
registration record, runtime overlay, concentration audit, figure manifest,
and figures be copied into `docs/chempas/musica/global-tropo-runs/` for review.
Full NetCDF, logs, restarts, executables, and TUV-x data remain external.
Publishing or committing that evidence is a separate repository action.

## Completed promotion result

The ladder completed on 2026-08-15. All eleven gates are passed and promotable
from science commit `caa0c12dde7b862ce14a49021e25a45cc00b337f` and one
`atmosphere_model` binary with SHA-256 `ff7166f1...31c2`. R3 passed all 45
assertions and F3 passed all 46. The portable publication contains no private
absolute paths and its manifest retains the hashes of the immutable source
receipts.

The final R3 NOx source was 6.774776721 Gmol and its
emissions-applied-minus-withheld burden difference was 6.774776720 Gmol,
leaving a -0.5733 mol residual. Its Ox residual was +0.01627 mol. The final F3
NOy source was 6.772250150 Gmol and its emissions-continued-minus-withheld
difference was 6.772250150 Gmol, leaving a -0.1771 mol residual. Each is many
orders of magnitude inside its declared tolerance. The inventory retained
93.243% NO and 6.757% NO2 by molecules; the 24-hour integrated source is
0.09489 Tg N, or 34.6 Tg N yr-1 if that July day were repeated.

All 70 hard concentration/geometry bounds and 44 broad reference-screening
checks pass. In the expanded emissions-continued lower troposphere, weighted
means are 0.0216 ppb NO, 0.1419 ppb NO2, 42.95 ppb O3, 0.5809 ppb HNO3,
1.896 ppm CH4, and 87.67 ppb CO. Across the pressure-at-least-150-hPa
diagnostic domain, mean OH is 1.326 million molecule cm-3. Expanded
lower-tropospheric O3 is 0.0510 ppb higher with emissions continued than with
emissions withheld during F3, while reduced O3 is 0.0544 ppb lower with
emissions applied than withheld during R3 through titration. These one-day
branch differences diagnose the mechanisms; they are not climatological ozone
effects.

The reported above-150-hPa O3 weighted mean is 2.095 ppm (p99 5.974 ppm). It is
stratospheric-like, but deliberately remains an unqualified stability
diagnostic because the mechanism does not represent stratospheric chemistry.
The complete statistics, source-grid extrema, physical interpretation,
resource costs, and evidence map are in
`global-tropo-runs/README.md`.

One operational detail is retained for reproducibility. The science-commit F3
runner's `split_first` directory contained the staged 00Z restart symlink and
mistook it for generated output. That one run-local symlink was removed after
the process started so the regular generated 12Z split boundary was selected;
the registered FS source and initialized state were untouched. The delivered
selector ignores staged symlinks and requires the exact generated timestamp.
All split/continuous state, source, photolysis, and budget comparisons passed.

## Failure semantics

- A normal MPAS exit is not a passed gate; the checker report is authoritative.
- A scientifically passed dirty run is explicitly non-promotable.
- Negative emissions, missing/non-finite state, solver failures, or any logged
  negative clipping fail the gate.
- F2/F3 refuse an unregistered, wrong-time, wrong-tier, or hash-changed FS
  restart.
- Plotting refuses failed reports, incomplete 24-hour runs, mixed provenance,
  unverified histories, or fewer than 300 dpi.
- No above-150-hPa output should be interpreted as qualified stratospheric
  chemistry, and no result from this ladder should be described as a
  regulatory or production air-quality prediction.
