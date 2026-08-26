# Global Tropospheric NOx Emissions Implementation Plan

**Status:** Completed and verified (2026-08-15)

**Target branch:** `develop_emissions`

**Planning baseline:** `9dde566b` (`docs: document MIEM emissions architecture`)

**Relationship to existing work:** This plan starts from the completed Phase 9
global MIEM implementation in `PLAN_EMISSIONS.md`. It must not replace, rename,
or reinterpret the accepted Chapman-NOx reports and external artifacts. New run
metadata and evidence live in a separate global-tropospheric namespace.

**Completion record (2026-08-15):** The complete clean same-commit ladder passed
at science commit `caa0c12dde7b862ce14a49021e25a45cc00b337f` with executable
SHA-256 `ff7166f1...31c2`. R0, R-CAL, R1, R2, R3, F0, F-CAL, F1, FS, F2, and
F3 are all passed and promotable. The immutable FS restart, continuous/split
comparisons, paired controls, source and family budgets, chemistry/rate tests,
physical concentration audit, compact portable receipts, and nine 300-dpi
PNG/PDF diagnostic pairs are verified under `chempas-science-plot-v1`,
including explicit reduced and expanded NO/NO2 tropospheric columns. The
science reports remain tied to the
science commit; later evidence-publication, audit, and restart-selection fixes
do not alter those model results. Detailed outcomes and limitations are in
`docs/chempas/musica/global-tropo-runs/README.md`.

## Goal

Create a reproducible global x1.40962 experiment that applies the existing
explicit CAMS-GLOB-ANT v6.2 NO and NO2 emissions through MIEM and evaluates them
with tropospheric chemistry.

Implementation proceeds through two chemistry tiers:

1. A reduced three-species NOx-O3 mechanism derived from the LNOx case. This is
   the inexpensive, strongly constrained source-response and coupling test.
2. The existing Ox-HOx-NOx-CO-CH4 mechanism, after its mesh-specific chemistry
   issues are resolved. This adds radical-mediated ozone production and an HNO3
   reservoir, but remains a reduced research mechanism rather than a production
   air-quality mechanism.

The work is complete when:

- both mechanisms contain exactly the `EMIS.NO` and `EMIS.NO2` reactions needed
  by the current MIEM inventory;
- the reduced mechanism passes global zero-source, science-hour, restart, and
  full-diurnal paired-control gates;
- the expanded mechanism passes box/rate qualification followed by global
  shakedown, spin-up, restart, and full-diurnal paired-control gates;
- initial conditions are generated reproducibly from the pinned date-matched
  GFS state without overwriting its water-vapor or meteorological fields;
- source mass, reactive-nitrogen, reduced-mechanism odd-oxygen, photolysis,
  restart, non-negativity, and resource contracts are checked automatically;
- the existing Stage 9 runner, reports, schemas, and hashes retain their current
  behavior; and
- documentation distinguishes software/process validation, reduced-mechanism
  interpretation, and production atmospheric-chemistry requirements.

## Settled decisions

- **Use the LNOx chemistry, not the LNOx source, for the first tier.** The
  operator-split lightning source remains disabled in every emissions-only gate.
- **MIEM is the only NOx source in the paired experiments.** A later explicitly
  named coexistence experiment may enable lightning, but it is not part of the
  acceptance ladder in this plan.
- **Preserve the inventory's explicit NO/NO2 fields.** The science inventory is
  already molecular-weight-normalized and speciated. Every CAMS species-map
  factor remains `1.0`; the synthetic 90/10 mapping is not applied again.
- **Keep the existing MIEM inventory and mesh contract unchanged.** No new
  horizontal remapping or runtime regridding is introduced.
- **Create combined MICM mechanisms.** MIEM requires `EMIS.NO` and `EMIS.NO2`
  in the selected MICM mechanism. The plain `lnox_o3.yaml` and
  `tropo_ch4nox.yaml` files do not satisfy that contract on their own.
- **Leave `miem_lnox_o3.yaml` as the short R5 coexistence fixture.** The new
  global reduced mechanism receives its own name and calibrated tolerances so
  this work does not silently change an accepted chem-box regression input.
- **Do not use `lnox_o3_sink.yaml`.** Its first-order relaxation is not a
  chemically resolved tropospheric sink, and its zero-rate behavior is already
  documented as unsafe.
- **Use TUV-x, not the fallback `jNO2`, in global acceptance runs.** Photolysis
  is recomputed from the absolute clock at every chemistry step for restart
  reproducibility. The fallback remains available only for isolated tests.
- **Use the real GFS `qv` field unchanged.** MICM H2O remains read-only and
  host-bound to MPAS `qv`; no `qH2O` tracer is created.
- **Keep accepted Stage 9 evidence immutable.** New scenario manifests, reports,
  schemas, figures, and derived initial-condition records use distinct names.
- **Treat all-column chemistry as an explicit experimental boundary.** The
  current coupler solves MICM at all 26 levels through the approximately 45-km
  model top. Tropospheric diagnostics are evaluated below a recorded tropopause
  mask; upper-column stability is audited separately. This plan does not claim
  that the expanded mechanism represents stratospheric chemistry.
- **Do not call the expanded tier production air quality.** It lacks deposition,
  detailed VOC chemistry, nighttime NO3/N2O5 chemistry, meteorology-dependent
  plume rise, and a chemically assimilated or multiweek-spun initial state.

## Scope

This plan includes:

- combined MICM mechanism files for reduced and expanded chemistry;
- a strict-JSON cleanup and validation test for TUV-x configurations;
- a pressure-dependent `OH + NO2 (+M) -> HNO3` rate for the expanded mechanism;
- mechanism parsing, reaction-inventory, elemental-N, and rate-matrix tests;
- reproducible reduced and expanded chemistry initial-condition preparation;
- a separate global-tropospheric scenario manifest and report schema;
- reusable staging/checking helpers without changing existing Stage 9 defaults;
- short global shakedowns, restart comparisons, matched no-MIEM controls, and
  full-diurnal experiments;
- solver-tolerance calibration for both mechanism tiers;
- external storage and hash manifests for large run inputs and histories;
- scientific plots and documentation bounded by the mechanism capabilities; and
- a hash-closed, pressure-banded physical concentration plausibility audit.

This plan does not include:

- acquiring or remapping a new emissions inventory;
- re-speciating the accepted CAMS explicit NO and NO2 fields;
- runtime horizontal regridding;
- online lightning, soil, fire, biogenic, or meteorology-dependent emissions;
- sector-specific stack heights or online plume rise;
- dry or wet deposition implementation;
- lateral-boundary support for runtime chemistry tracers;
- a unified troposphere-stratosphere production mechanism;
- chemical data assimilation; or
- a claim that a one-day experiment is a climatology or regulatory forecast.

## Chemistry tiers

| Tier | Planned MICM file | Species relevant to the acceptance budget | TUV-x file | Interpretation |
|---|---|---|---|---|
| Reduced | `micm_configs/global_cams_lnox_o3.yaml` | NO, NO2, O3 | `micm_configs/tuvx_no2.json` | Leighton cycling, NO titration, and source/transport validation |
| Expanded | `micm_configs/global_cams_tropo_ch4nox.yaml` | NO, NO2, HNO3, O3, HOx, CO, CH4, reservoirs | `micm_configs/tuvx_tropo.json` | Reduced Ox-HOx-NOx-CO-CH4 response with radical-mediated ozone production |

The combined files are deliberate, reviewable snapshots. Tests must prove that
each file retains the complete non-emission reaction list and species properties
from its source mechanism, apart from explicitly reviewed chemistry corrections
and solver tolerances, and adds exactly these reactions:

```yaml
- type: EMISSION
  gas phase: gas
  name: NO
  products:
    - species name: NO
      coefficient: 1

- type: EMISSION
  gas phase: gas
  name: NO2
  products:
    - species name: NO2
      coefficient: 1
```

No other `EMIS.*` rate is allowed while the selected MIEM configuration returns
only NO and NO2.

## Required scientific and software contracts

### Reduced-mechanism budget contract

The reduced reactions are:

```text
NO + O3  -> NO2
NO2 + hv -> NO + O3
```

For a closed global domain, define molar burdens from MPAS dry-air mass and the
species molar masses:

```text
NOx = n(NO) + n(NO2)
Ox  = n(O3) + n(NO2)
```

The chemistry exactly conserves both quantities. Therefore, after subtracting a
matched no-MIEM control:

```text
delta NOx = integrated emitted moles(NO) + integrated emitted moles(NO2)
delta Ox  = integrated emitted moles(NO2)
```

The checker evaluates cumulative and adjacent-output forms of both identities.
It uses combined relative/absolute tolerances derived from zero-source and
strict-solver reference runs; it does not weaken a failed budget by normalizing
against the large background burden.

The reduced tier must also demonstrate:

- `jNO2 == 0` in local night and positive finite values in local daylight;
- nonnegative finite NO, NO2, and O3 after the MICM boundary clipping contract;
- an enabled-minus-control NO2 response spatially associated with the NOx
  source; and
- O3 titration in at least one declared high-NO source region, reported as a
  science diagnostic rather than forced as a global-sign assertion.

### Expanded-mechanism nitrogen contract

For the current expanded mechanism, reactive nitrogen is:

```text
NOy = n(NO) + n(NO2) + n(HNO3)
```

All enabled gas reactions must conserve elemental nitrogen. With deposition and
other nitrogen sources disabled, the matched-control response must satisfy:

```text
delta NOy = integrated emitted moles(NO) + integrated emitted moles(NO2)
```

This identity is checked at every output interval and cumulatively. Individual
NO and NO2 tracer changes are not compared directly with their emitted masses
because chemistry repartitions nitrogen into HNO3.

The expanded tier must additionally report, without imposing an unsupported
exact conservation law:

- tropospheric O3 enabled-minus-control burden and maps;
- NO/NO2/HNO3 partitioning;
- OH and HO2 daylight distributions and diurnal cycles;
- CO and CH4 changes;
- all eight configured photolysis rates;
- tropopause-separated and full-column burdens; and
- upper-column drift caused by applying a tropospheric mechanism above the
  tropopause.

### Pressure-dependent HNO3 formation contract

Before the expanded mechanism can enter a global gate, replace its fixed
950-hPa effective `OH + NO2 -> HNO3` Arrhenius rate with MICM's native `TROE`
form using the reviewed low-pressure, high-pressure, and broadening parameters.

Qualification must compare the MICM rate against an independent implementation
over at least this matrix:

- temperatures: 220, 250, 280, and 300 K;
- pressures: 100, 300, 700, and 1000 hPa; and
- a tight numerical tolerance appropriate to the identical analytic formula.

The test must also prove that pressure is taken from each MPAS/MICM grid cell,
not fixed by the mechanism-preparation script. A mechanism that retains the
current fixed-pressure approximation cannot advance past the expanded box gate.

### Initial-condition contract

The preparation workflow starts from the pinned date-matched
`mpas-x1.40962-gfs-20240701t00z-state` artifact and writes a new file rather
than editing it in place.

For both chemistry tiers it must:

- preserve dimensions, mesh identity, clock, and non-chemistry variables;
- preserve `qv` bitwise;
- derive layer-center height from `zgrid` with its actual NetCDF dimension
  ordering rather than assuming an in-memory orientation;
- write finite, nonnegative mass mixing ratios with units and long names;
- include a global ozone profile with a plausible tropospheric background and
  overhead stratospheric column for TUV-x;
- write declared background NO and NO2 profiles rather than inheriting the
  Chapman-NOx initialization accidentally;
- omit `qH2O`, because H2O is host-bound to `qv`;
- record profile equations, constants, input/output SHA-256 values, mesh
  fingerprint, ozone column statistics, and global initial burdens in an audit;
  and
- fail if an existing output would be overwritten without an explicit
  replacement option.

The expanded tier also initializes O2, CO, CH4, H2O2, CH2O, CH3OOH, and HNO3.
Fast radicals O, O1D, OH, HO2, and CH3O2 start at zero unless a qualified spin-up
artifact supplies them. The third body `M` is derived by MICM and is not an MPAS
tracer.

### Photolysis contract

- `tuvx_no2.json` and `tuvx_tropo.json` must parse with a strict RFC-compatible
  JSON parser before TUV-x sees them.
- TUV-x reaction names must match MICM `PHOTO.<name>` parameters one-to-one.
- The reduced mechanism exposes only `jNO2`.
- The expanded mechanism exposes exactly `jO3_O1D`, `jO3_O`, `jNO2`, `jH2O2`,
  `jCH2O_a`, `jCH2O_b`, `jCH3OOH`, and `jHNO3`.
- Global acceptance uses grid-cell latitude/longitude and per-chemistry-step
  recomputation from absolute time.
- The model-top extension begins at the actual model edge and is hash-recorded.
- Day/night, branch-ratio, restart, and complete-diurnal checks remain distinct;
  one passing maximum value cannot substitute for the spatial/temporal audit.

### Emissions contract

- Use `miem_configs/global_cams_nox.yaml` unchanged for science runs.
- Keep all 13 accepted sectors and explicit species-map scaling factors of 1.0.
- Validate the inventory against the exact initial-condition mesh before every
  gate.
- Keep current surface injection for the acceptance ladder and state that it is
  not plume rise.
- Keep `config_lnox_source_rate = 0` and verify from metadata/logs that lightning
  is disabled.
- Preserve MIEM source diagnostics and final emitted-mass logs independently of
  chemistry tracer changes.

### Vertical interpretation contract

The runner derives a diagnostic tropopause mask from a documented rule selected
during preflight. Prefer a pressure- or thermodynamic-tropopause field already
present in the initialized state; if none is available in history output, use a
fixed pressure threshold only after recording that simplification.

Every expanded report contains both:

- tropospheric diagnostics using the recorded mask; and
- full-column/above-tropopause stability diagnostics exposing behavior outside
  the mechanism's intended domain.

Passing this plan does not make the upper atmosphere scientifically valid. A
future production phase must either use a unified mechanism or add a qualified
vertical chemistry-domain treatment.

### Evidence and immutability contract

- Existing `docs/chempas/musica/global-runs/stage9*.json` files are read-only
  inputs to regression checks, never output targets for this plan.
- New reports live below `docs/chempas/musica/global-tropo-runs/`.
- Large NetCDF histories, restarts, logs, and executables remain below the
  external data root.
- Every compact report records configuration, code, dependency, executable,
  initial-condition, inventory, partition, TUV-x-data, and selected-history
  hashes.
- A promotion gate refuses to mix reduced and expanded mechanisms, candidate and
  reference tolerances, different meshes, different initial states, or different
  executables unless the comparison explicitly declares that axis.
- Existing Stage 9 unit tests and static report validation must pass after every
  harness refactor.

## Stage 0 — Preflight and contract freeze

### Tasks

- [x] Record the exact CheMPAS-A, MUSICA, MICM, MIEM, and TUV-x revisions used
  for implementation and runs.
- [x] Confirm the pinned MICM parser and solver support `TROE` in the same
  single-file mechanism format used by CheMPAS-A.
- [x] Select and document the independent kinetic expression and parameter set
  for `OH + NO2 (+M) -> HNO3`.
- [x] Inventory the exact species, reactions, rate parameters, and TUV-x names in
  both source mechanisms.
- [x] Confirm that the accepted CAMS file spans every planned spin-up and
  analysis timestamp.
- [x] Select the diagnostic tropopause rule and confirm all necessary pressure or
  tropopause fields are available in history output.
- [x] Estimate wall time, peak RSS, history volume, restart volume, and required
  free disk space for each gate before launching it.
- [x] Capture hashes of the completed Stage 9 reports that the regression test
  must continue to accept unchanged.

### Gate

- [x] A short MICM reproducer successfully parses and evaluates one `TROE`
  reaction with cell-varying temperature and pressure.
- [x] The chosen expanded chemistry parameters and tropopause rule are written
  into the plan or a linked design note; neither remains an implicit runtime
  choice.
- [x] Inventory time coverage and resource estimates cover the full ladder.
- [x] No planned output path aliases a completed Stage 9 artifact.

## Stage 1 — Mechanism and photolysis assets

### Files

- `micm_configs/global_cams_lnox_o3.yaml`
- `micm_configs/tropo_ch4nox.yaml`
- `micm_configs/global_cams_tropo_ch4nox.yaml`
- `micm_configs/tuvx_no2.json`
- `micm_configs/README.md`
- `tests/test_global_tropo_mechanisms.py`

### Tasks

- [x] Remove the trailing comma from `tuvx_no2.json` and add strict parsing of
  every tracked MICM/TUV-x JSON configuration to the test suite.
- [x] Build `global_cams_lnox_o3.yaml` from `lnox_o3.yaml`, add exactly two
  emission reactions, and use candidate global tolerances that will be accepted
  or replaced only through Stage 4 calibration.
- [x] Replace the fixed-pressure HNO3 formation reaction in
  `tropo_ch4nox.yaml` with the qualified `TROE` reaction.
- [x] Build `global_cams_tropo_ch4nox.yaml` from the corrected expanded source
  mechanism and add exactly two emission reactions.
- [x] Add static tests for species names, molar masses, host-bound H2O behavior,
  reaction names/types, emission targets, photolysis names, and elemental-N
  balance.
- [x] Add a rate-matrix test for HNO3 formation across the Stage 0 T/P matrix.
- [x] Extend the mechanism README with the distinction between LNOx-derived
  reduced chemistry and the expanded experimental mechanism.

### Gate

- [x] Both combined mechanisms parse through the pinned MICM configuration path.
- [x] MIEM species discovery maps one-to-one to writable `NO`/`NO2` species and
  `EMIS.NO`/`EMIS.NO2` parameters.
- [x] Strict JSON parsing and MICM/TUV-x name matching pass.
- [x] The independent and MICM Troe rates pass the complete T/P matrix.
- [x] Every non-emission nitrogen reaction is elementally balanced.

## Stage 2 — Reproducible chemistry initial conditions

### Files

- `scripts/prepare_global_tropo_initial_condition.py`
- `tests/test_prepare_global_tropo_initial_condition.py`
- `test_cases/global_tropo_miem/external-inputs.overlay.json`
- `test_cases/global_tropo_miem/external-inputs.overlay.schema.json`
- `docs/chempas/musica/global-tropo-runs/initial-condition-audits/`

### Tasks

- [x] Factor reusable, pure profile calculations from `scripts/init_tropo.py`
  without changing that script's existing behavior.
- [x] Add `--mechanism reduced|expanded` and explicit input/output/report options.
- [x] For the reduced state, write only qNO, qNO2, and qO3 chemistry tracers.
- [x] For the expanded state, write every non-third-body, non-host-bound
  mechanism tracer, including zero-valued fast radicals.
- [x] Preserve `qv` and all meteorological fields bitwise and verify this in the
  audit rather than relying on copy semantics.
- [x] Compute and report ozone-column and initial NOx/NOy statistics globally,
  by hemisphere, and below/above the selected tropopause.
- [x] Create external derived-artifact records containing size and SHA-256 values
  without copying the large NetCDF files into Git.
- [x] Implement an overlay resolver that pins the existing Stage 9 base manifest
  plus the new derived artifacts and rejects conflicting duplicate IDs.

### Gate

- [x] Repeating preparation from the same input produces byte-identical output
  and audit JSON.
- [x] Both outputs pass exact mesh-identity validation.
- [x] `qv` and all non-chemistry arrays are bitwise equal to the source state.
- [x] There is no qH2O or qM variable and every required non-third-body,
  non-host-bound tracer exists.
- [x] All chemistry values and reported columns/burdens are finite, nonnegative,
  and within declared initialization bounds.

## Stage 3 — Reusable global-tropospheric harness

### Files

- `test_cases/global_tropo_miem/scenarios.yaml`
- `test_cases/global_tropo_miem/README.md`
- `test_cases/global_tropo_miem/stream_list.atmosphere.throughput`
- `test_cases/global_tropo_miem/throughput-report.schema.json`
- `scripts/global_miem_harness.py`
- `scripts/run_global_tropo_miem_integration.py`
- `scripts/check_global_tropo_miem_throughput.py`
- `tests/test_global_tropo_miem_harness.py`

### Design

Extract only side-effect-free, mechanism-neutral staging utilities from the
existing Stage 9 runner/checker into `global_miem_harness.py`. Existing command
lines, scenario defaults, report paths, report schemas, and serialized output
must remain unchanged. The new runner supplies its own manifest, gate sequence,
chemistry field list, nitrogen-family definition, photolysis list, and report
namespace.

The new checker is mechanism-aware through an explicit manifest contract; it
must not infer the active mechanism from whichever fields happen to be present.

### Tasks

- [x] Add separate gate IDs and promotion paths for reduced (`R*`) and expanded
  (`F*`) chemistry.
- [x] Parameterize the staged MICM/TUV-x files and output chemistry diagnostics.
- [x] Keep emission species fixed to NO and NO2 while allowing chemistry budget
  families to differ by tier.
- [x] Add the reduced NOx and Ox burden audits.
- [x] Add the expanded NOy audit and tropopause-separated diagnostics.
- [x] Preserve existing source, sector, layer, grid, interpolation, reader,
  restart, resource, and finite-state audits where applicable.
- [x] Add strict preflight for mechanism identity, initial-condition identity,
  lightning-disabled state, inventory time coverage, available disk, and output
  field capacity.
- [x] Add a dry-run/stage-only mode that writes the fully resolved configuration
  and predicted storage cost without launching MPI.
- [x] Test report schema rejection for missing, extra, NaN, mixed-tier, and
  mixed-executable data.

### Gate

- [x] All existing Stage 9 Python/Fortran static and harness tests pass without
  rewriting any accepted report.
- [x] The new runner can stage reduced and expanded zero-source cases in a
  temporary directory with the expected files and no source-tree writes.
- [x] The new checker passes deterministic synthetic fixtures for reduced NOx/Ox
  and expanded NOy budgets, and fails deliberately perturbed fixtures.
- [x] Stage-only metadata contains every required provenance hash and reports
  lightning disabled.

## Stage 4 — Reduced global mechanism qualification

### R0: zero-source identity

- Five-minute global run from the reduced initial state.
- Variants: MIEM disabled and MIEM enabled with an exact zero inventory.
- Require bitwise identity for all common dynamics, chemistry, and photolysis
  fields; zero emission diagnostics; no MIEM work in the disabled variant; and a
  complete enabled MIEM lifecycle in the zero variant.

### R-CAL: solver-tolerance calibration

- Run the same short nonzero synthetic source with a strict reference tolerance
  set and the candidate production tolerances.
- Require bounded elementwise tracer differences, reduced NOx/Ox budget closure,
  no new clipping, identical non-chemistry fields, and a recorded wall-time
  comparison.
- Update candidate per-species absolute tolerances only from this evidence.

### R1: one-hour science shakedown

- Use the accepted CAMS inventory and reduced GFS chemistry state.
- Variants: enabled and matched no-MIEM control.
- Require source/sector/layer closure, NOx and Ox response closure, TUV-x
  day/night behavior, finite nonnegative state, meteorology identity against the
  control, and stable resources.

### R2: six-hour restart gate

- Variants: continuous, 3+3-hour restart, and matched no-MIEM control.
- Recompute TUV-x every chemistry step from absolute time.
- Require bitwise emissions/meteorology and bounded elementwise chemistry/
  photolysis restart equivalence at every common timestamp.

### R3: 24-hour diurnal acceptance

- Variants: continuous, 12+12-hour restart, and matched no-MIEM control.
- Hourly output with complete local-day/local-night sampling.
- Require all R1/R2 contracts plus cumulative and interval NOx/Ox closure,
  complete diurnal photolysis, hemispheric and vertical source/response audits,
  selected urban/remote response diagnostics, and stable disk/RSS/timer behavior.

### Reduced-tier gate

- [x] R0, R-CAL, R1, R2, and R3 reports all pass and share the declared build,
  mesh, partition, inventory, and reduced initial state.
- [x] The selected candidate tolerances and their reference comparison are
  recorded in the combined mechanism and compact report.
- [x] The reduced result is labeled source-response/Leighton-cycle validation,
  not net tropospheric ozone-production chemistry.

## Stage 5 — Expanded chemistry qualification and spin-up

### F0: box and column qualification

- [x] Run zero-dimensional daytime, nighttime, low-NOx, high-NOx, and pressure
  matrix cases.
- [x] Verify radical spin-up, NOx-to-HNO3 transfer, photolysis branching, finite
  state, non-negativity, and elemental-N conservation.
- [x] Compare the corrected Troe mechanism against the independent rate
  implementation and retain machine-readable results.
- [x] Run a one-column diurnal case using representative lower-, middle-, and
  upper-tropospheric T/P/H2O profiles before paying for a global integration.

### F-CAL: global solver calibration

- [x] Compare candidate species-specific tolerances with a stricter reference on
  a short global state that includes daylight, darkness, humid lower-troposphere,
  dry upper-troposphere, source, and no-source cells.
- [x] Bound every species elementwise, preserve NOy closure, reject new clipping
  or solver failures, and record the performance ratio.

### F1: one-hour global shakedown

- [x] Run expanded chemistry with CAMS enabled and a matched no-MIEM control.
- [x] Require exact source closure, reactive NOy closure, finite/nonnegative
  state, eight-rate TUV-x coverage, H2O-to-qv host-binding evidence, and stable
  resources.
- [x] Report OH/HO2 distributions and upper-column drift without yet treating
  their magnitudes as an acceptance threshold.

### FS: common 24-hour spin-up

- [x] Starting from the expanded idealized chemistry state, run one complete
  diurnal cycle with CAMS emissions enabled.
- [x] Require NOy/source closure, finite state, radical day/night cycling, and no
  solver failure or unbounded upper-column drift.
- [x] Write a restart exactly at the analysis boundary and register its size,
  hash, chemistry mechanism, executable, and parent state in the external
  overlay manifest.
- [x] State explicitly that one day initializes fast radicals and diurnal
  partitioning; it is not a multiweek chemical spin-up of long-lived species.

### Expanded qualification gate

- [x] F0, F-CAL, F1, and FS pass before the expanded 24-hour experiment begins.
- [x] The spin-up restart is immutable, hash-verified, and used by every F2/F3
  variant.

## Stage 6 — Expanded global acceptance

### F2: six-hour restart and response gate

- Start every variant from the qualified common spin-up restart.
- The matched control uses the same emissions-enabled spin-up and disables MIEM
  only for the six-hour analysis window. The reported response therefore means
  continued source versus source removal from an identical chemical state.
- Variants: continuous enabled, 3+3-hour enabled restart, and matched no-MIEM
  control.
- Require emissions and meteorology identity, bounded chemistry/photolysis
  restart equivalence, interval/cumulative NOy closure, eight-rate photolysis,
  finite state, and stable resources.

### F3: 24-hour diurnal experiment

- Start every variant from the qualified common spin-up restart.
- As in F2, the control disables MIEM only after the common spin-up boundary.
- Variants: continuous enabled, 12+12-hour enabled restart, and matched no-MIEM
  control.
- Require all F2 contracts across 25 hourly frames.
- Diagnose enabled-minus-control tropospheric O3, NOx, HNO3, OH, HO2, CO, and CH4.
- Audit global, hemispheric, vertical, sector, urban/remote, daylight/nighttime,
  tropospheric, and above-tropopause distributions.
- Require NOy response/source closure; do not require a predetermined sign for
  global O3 because the reduced chemical environment can be NOx-limited or
  titration-dominated by region and time.
- Record full timing, RSS, solver failure/clipping, history size, and restart size
  telemetry and compare them with the reduced R3 run.

### Expanded-tier gate

- [x] F2 and F3 reports pass and reproduce from the pinned spin-up state.
- [x] No report hides above-tropopause behavior by presenting only filtered
  tropospheric diagnostics.
- [x] Scientific text remains within the declared reduced-mechanism boundary.

## Stage 7 — Reproducibility, visualization, and documentation

### Files

- `scripts/plot_global_tropo_miem.py`
- `scripts/audit_global_tropo_concentrations.py`
- `scripts/publish_global_tropo_evidence.py`
- `docs/chempas/musica/GLOBAL_TROPOSPHERIC_NOX.md`
- `docs/chempas/musica/global-tropo-runs/*.json`
- `docs/chempas/musica/global-tropo-runs/figures/`
- `docs/chempas/musica/global-tropo-runs/figure-manifest.json`
- updates to `EMISSIONS.md`, `RUN.md`, and relevant indexes

### Required figures

- final instantaneous global NO and NO2 surface-emission fluxes;
- reduced emissions-applied and emissions-applied-minus-withheld NO/NO2 column
  burdens for the diagnostic troposphere;
- reduced hourly NO/NO2 burden evolution plus cumulative NOx and Ox closure;
- expanded emissions-continued and emissions-continued-minus-withheld NO/NO2
  column burdens for the diagnostic troposphere;
- expanded NO/NO2/HNO3 tropospheric burden evolution, partition, and NOy
  closure;
- expanded tropospheric O3/HNO3/OH/HO2 column response;
- vertical/tropopause-separated response and upper-column drift; and
- reduced-versus-expanded wall time, RSS, and output-volume comparison.

### Tasks

- [x] Make plotting refuse failed reports, mixed provenance, or unverified input
  hashes.
- [x] Store raster and vector figures with a deterministic style and manifest.
- [x] Apply the versioned plotting protocol: Title Case figure titles, UTC
  subtitles, lettered sentence-case panels, explicit domains/comparisons, and
  pressure decreasing upward.
- [x] Label endpoint fields as instantaneous snapshots rather than daily means,
  and name the emissions intervention instead of using `enabled`, `forcing`, or
  an unqualified `control` in public plot text.
- [x] Audit exact extrema and weighted concentration ranges in lower-
  tropospheric, upper-tropospheric, and unqualified upper-column pressure bands.
- [x] Document exact preparation, staging, run, checking, and plotting commands.
- [x] Document how to reproduce only the reduced ladder when resources do not
  permit the expanded experiment.
- [x] Add a limitations section covering initial conditions, spin-up, deposition,
  VOC complexity, nighttime chemistry, surface-only injection, model-top scope,
  and clear-sky/cloud assumptions.
- [x] Run the complete unit/static test suite, mechanism reproducers, strict JSON
  checks, and `git diff --check`.

### Final gate

- [x] Every required compact report and figure manifest validates against its
  schema and all referenced external files pass size/hash verification.
- [x] Existing Stage 9 release-evidence tests still pass unchanged.
- [x] The documentation can reproduce both tiers from a clean checkout plus the
  declared external data root.
- [x] The final summary explicitly separates these conclusions:
  - MIEM/global coupling correctness;
  - reduced NOx-O3 process response;
  - expanded reduced-mechanism chemistry response; and
  - capabilities still required for production atmospheric chemistry.

## Promotion ladder summary

| Gate | Duration | Mechanism | Main purpose | Promotion requirement |
|---|---:|---|---|---|
| R0 | 5 min | Reduced | Zero-source identity | Bitwise common fields and correct MIEM lifecycle |
| R-CAL | short | Reduced | Solver calibration | Bounded state/budgets with recorded cost |
| R1 | 1 h | Reduced | Science-inventory shakedown | Source, NOx, Ox, photolysis, finite state |
| R2 | 6 h | Reduced | Restart | Continuous/split equivalence and paired control |
| R3 | 24 h | Reduced | Diurnal acceptance | Complete budget/distribution/resource audit |
| F0 | box/column | Expanded | Chemical qualification | Troe/radical/NOy/photolysis contracts |
| F-CAL | short | Expanded | Solver calibration | Species-wise accuracy and stable performance |
| F1 | 1 h | Expanded | Global shakedown | Source/NOy/host-binding/eight-rate stability |
| FS | 24 h | Expanded | Common fast-chemistry spin-up | Qualified immutable restart |
| F2 | 6 h | Expanded | Restart/response | Continuous/split/control equivalence |
| F3 | 24 h | Expanded | Diurnal experiment | Full NOy/science/distribution/resource audit |

## Planned tracked artifacts

```text
PLAN_GLOBAL_TROPOSPHERIC_NOX.md
micm_configs/
  global_cams_lnox_o3.yaml
  global_cams_lnox_o3_strict.yaml
  global_cams_tropo_ch4nox.yaml
  global_cams_tropo_ch4nox_strict.yaml
test_cases/global_tropo_miem/
  README.md
  scenarios.yaml
  throughput-report.schema.json
  f0-report.schema.json
  figure-manifest.schema.json
  concentration-audit.schema.json
  evidence-publication.schema.json
  external-inputs.overlay.json
  external-inputs.overlay.schema.json
  stream_list.atmosphere.throughput
scripts/
  global_miem_harness.py
  tropo_profiles.py
  prepare_global_tropo_initial_condition.py
  run_global_tropo_f0.py
  run_global_tropo_miem_integration.py
  check_global_tropo_miem_throughput.py
  register_global_tropo_spinup_restart.py
  plot_global_tropo_miem.py
  audit_global_tropo_concentrations.py
  publish_global_tropo_evidence.py
tests/
  cpp/qualify_global_tropo_chemistry.cpp
  cpp/test_global_tropo_troe.cpp
  test_global_tropo_mechanisms.py
  test_prepare_global_tropo_initial_condition.py
  test_global_tropo_miem_harness.py
  test_global_tropo_concentrations.py
docs/chempas/musica/
  GLOBAL_TROPOSPHERIC_NOX.md
  global-tropo-runs/
    initial-condition-audits/
    reduced-*.json
    expanded-*.json
    figures/
    figure-manifest.json
```

Generated NetCDF states, histories, restarts, full logs, and executables remain
outside Git beneath `CHEMPAS_EMISSIONS_DATA_ROOT` and are referenced by hash.

## Checkpoint discipline

- Implement one stage or separately named gate at a time.
- Before a checkpoint, run its scoped tests plus the unchanged Stage 9 static
  regression suite and `git diff --check`.
- Stage only files belonging to that checkpoint; preserve unrelated user files
  and generated data.
- Do not mark a global gate complete from a clean model exit alone. Its checker
  report must pass every declared assertion.
- Do not advance from reduced to expanded chemistry merely because R3 passes;
  F0 and the pressure-dependent chemistry gate are mandatory.
- Record commit, dependency, executable, configuration, and external-artifact
  hashes at every run checkpoint. Publishing or pushing checkpoints requires
  separate user authorization at implementation time.

## Final completion checklist

- [x] Reduced and expanded combined mechanisms expose exactly NO and NO2
  emissions.
- [x] Lightning is disabled throughout the emissions-only ladder.
- [x] Strict JSON and MICM/TUV-x reaction-name validation pass.
- [x] The expanded HNO3 formation rate is pressure dependent and independently
  verified.
- [x] Initial states are deterministic, exact-grid, and preserve GFS `qv` and
  meteorology bitwise.
- [x] R0 through R3 pass with calibrated solver tolerances.
- [x] F0, F-CAL, F1, FS, F2, and F3 pass with one immutable spin-up restart.
- [x] Reduced NOx/Ox and expanded NOy budgets close at every required interval.
- [x] Restart, control, day/night, finite-state, clipping, resource, and
  provenance contracts pass.
- [x] Tropospheric and above-tropopause diagnostics are both reported.
- [x] Existing Stage 9 reports and tests remain valid and unchanged.
- [x] Reproduction documentation and hash-verified figures are complete.
- [x] No result is described as production air quality without the additional
  mechanisms, sinks, emissions, initialization, and spin-up that this plan
  explicitly leaves out.
