# Global Tropospheric Methane and MOZART-35

## Current Status

The complete software path is implemented for global methane backgrounds and
surface exchange while retaining the accepted CAMS NO and NO2 emissions. This
includes the reduced Tier C mechanism, the generated MOZART-35 Tier Z
mechanism, run ladders, fail-closed checks, and protocol-compliant plots.

Actual science promotion is currently stopped at the data-access boundary. The
CAMS catalogue confirms the pinned v24r2 surface-plus-satellite product, but
this machine has no ADS credential. No inversion field, global methane run, or
science plot is represented as complete. The exact status is recorded in
[`global-methane-runs/d0-data-access-status.md`](global-methane-runs/d0-data-access-status.md).
The accepted legacy Tier C state has been expanded into a real, audited Tier Z
state with explicit `legacy_background` CH4 lineage. Current disk capacity is
also below the frozen requirement for the seven-day Tier Z paired gates; see
[`runtime-readiness-status.json`](global-methane-runs/runtime-readiness-status.json).

## Experiment Meaning

Two methane inputs are independent experiment axes:

- a three-dimensional CAMS CH4 dry-mole-fraction field initializes the
  atmosphere once; and
- a time-varying CH4 surface exchange is applied through MIEM.

The primary surface exchange is the signed posterior total from the same CAMS
inversion release as the atmospheric background. Its wetlands, rice,
biomass-burning, and provider-defined `other` fields sum to the total. Negative
values are downward uptake and are never clipped. CAMS-GLOB-ANT v6.2 CH4 is a
separate anthropogenic attribution source and is never added to the posterior
total.

Every paired methane experiment retains the accepted NO and NO2 emissions in both members.
The physical labels are:

- Surface Source Applied
- Surface Source Withheld
- Surface Source Continued
- Applied Minus Withheld
- Continued Minus Withheld

A withheld member is not an emissions-free atmosphere: it retains NO and NO2
surface sources, its initialized methane background, and any methane inherited
from a common spin-up. Public plots do not use `enabled`, `disabled`,
`forcing`, or an unqualified `control` as emission synonyms.

## Frozen Configuration

Required gates use:

- x1.40962 global mesh with 26 vertical levels;
- eight MPI ranks and the pinned eight-rank partition;
- 2024-07-01 00:00 UTC start;
- 450 s dynamics step;
- hourly history records;
- per-step TUV-x updates;
- accepted CAMS-GLOB-ANT v6.2 NO and NO2 exact-grid inventory; and
- no lightning NOx.

Tier C is the accepted reduced Ox-HOx-NOx-CO-CH4 chemistry plus `EMIS.CH4`.
Tier Z is the deterministic 35-transported-tracer MOZART-4 subset generated
from the pinned repository-local source. Tier Z also integrates five
reaction-driven bookkeeping tracers and binds O2, N2, and H2O as explicit
read-only host parameters. That binding is mechanism metadata-driven, so the
accepted Chapman and Tier C mechanisms continue to transport `qO2` unchanged.

## Data and Initialization Contracts

The pinned source records are summarized by the
[`data-access status`](global-methane-runs/d0-data-access-status.md) and its
neighboring audit records:

- the CAMS inversion v24r2 request and catalogue audit;
- the CAMS-GLOB-ANT v6.2 CH4 acquisition and conservative-remap audits; and
- the NOAA July 2024 monthly-mean benchmark audit.

The CAMS initializer remaps dry-air and methane moles separately in the
horizontal, remaps both through exact pressure-layer overlap, and reconstructs
the destination dry-air mole fraction. It writes dry-air mass mixing ratio as

```text
qCH4 = xCH4 × 0.016043 / 0.0289644
```

The audit checks global burden closure, provider XCH4, marine-boundary-layer
plausibility against NOAA, and bitwise preservation of meteorology, water
vapor, mesh, and clock. The Tier Z initializer preserves CAMS CH4 bitwise,
preserves common Tier C tracers, applies versioned profiles to additional
long-lived species, initializes fast intermediates before mandatory spin-up,
and records a provenance class for every tracer. It requires the incoming CH4
lineage to be declared exactly as `cams_inversion` or `legacy_background`, so a
legacy profile cannot be mislabeled as CAMS. The passing real legacy-state
record is
[`tier-z-legacy-initial-condition-audit.json`](global-methane-runs/tier-z-legacy-initial-condition-audit.json).
The runtime-manifest builder opens all four initial states and verifies qCH4
plus the exact Tier/lineage attributes. The gate runner repeats that check and
records the validated contract in its stage and run metadata.

## Surface Exchange and Accounting

MIEM opens separate exact-grid NOx and CH4 inventories. A two-inventory
compiled contract proves independent discovery and summation. Signed exchange
is opt-in by exact species name through `config_miem_net_flux_species`; all
other species retain the nonnegative source-only rule.

Runtime checks independently sample each inventory at every model step and
close applied mass against model diagnostics. Reaction-integrated C, N, and S
terminal ledgers distinguish chemical transfer from surface exchange. CH4 loss
through OH and O(1D) has separate integrated counters, so the reported
model-domain lifetime is derived from actual chemical loss rather than from a
short-run burden slope.

## MOZART-35 Qualification

`scripts/generate_micm_mozart35.py` consumes the pinned source and generates
normal/strict MICM configurations, a source mapping, generation manifest, and
18-channel TUV-x configuration. Generation fails on an unknown rate form,
unmapped product, source-hash change, or count mismatch.

The qualification contains 35 source tracers, 71 gas reactions, 18 photolysis
reactions, three emission entry points, five bookkeeping tracers, and three
host parameters. `scripts/test_mozart35_box.sh` compares the actual MICM
Rosenbrock solver with an independent SciPy BDF implementation for 48 hours
under a midpoint diurnal photolysis cycle. It checks all state variables,
major-species parity, and C/N/S conservation.

## Promotion Ladder

The required reports, in dependency order, are:

| Tier C | Purpose | Tier Z | Purpose |
|---|---|---|---|
| C1 | one-hour posterior-source shakedown | Z1 | one-hour MOZART-35 shakedown |
| CPS | 48-hour posterior common spin-up | ZPS | 48-hour radical spin-up |
| C2 | six-hour restart equivalence | Z2 | 24-hour restart and ledger equivalence |
| C3 | 24-hour posterior response pair | Z3 | seven-day posterior response pair |
| CAS | 48-hour anthropogenic spin-up | ZAS | 48-hour anthropogenic spin-up |
| CA3 | 24-hour anthropogenic attribution | ZA3 | seven-day anthropogenic attribution |
| CB3 | CAMS-minus-legacy background pair | ZB3 | CAMS-minus-legacy background pair |

Z4 is an optional 30-day extension and is not part of required publication.
Each gate is resolved from
[`scenarios.yaml`](../../_downloads/global-methane/scenarios.yaml),
requires its declared predecessor, and records a common source commit and
executable SHA-256. A model exit code alone is never a promotion result;
`scripts/check_global_methane_runs.py` must produce a passing, promotable
report.

## Plot Protocol

All methane figures follow
[`chempas-science-plot-v1`](../guides/PLOTTING_PROTOCOL.md):

- concise Title Case main titles;
- a subtitle with gate, complete UTC range, spatial/vertical domain,
  comparison, and time semantics;
- absolute CH4, NO, and NO2 diagnostic-tropospheric column burdens;
- explicit CH4, NO, and NO2 paired column responses;
- initial surface CH4, XCH4, and latitude-pressure structure;
- surface CH4, NO, and NO2 sources with inventory brackets;
- XCH4 and burden histories;
- carbon/source/loss, oxidation/ozone, photolysis/day-night, nitrogen, and
  vertical-structure diagnostics; and
- zero-centered symmetric scales for signed differences.

A final history map is instantaneous. A plot is labeled Daily Mean only after
explicit trapezoidal integration over a complete UTC day. Each 300 dpi PNG has
a vector PDF counterpart. Plotting begins only from a passing hash-verified
report, and publication requires every selected image to have an explicit
visual-inspection attestation.

## Reproduction Workflow

Create or update the supported environment and declare the external data root:

```bash
conda env update -n mpas -f environment.yml
export CHEMPAS_EMISSIONS_DATA_ROOT=/path/to/chempas-emissions-science
```

After accepting the CAMS dataset terms and configuring an ADS credential,
retrieve the frozen inversion requests:

```bash
conda run -n mpas python scripts/acquire_cams_methane_inversion.py acquire \
  --requests test_cases/global_methane/cams-inversion-v24r2-requests.json \
  --report "$CHEMPAS_EMISSIONS_DATA_ROOT/cams/inversion/v24r2/acquisition.json" \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT"
```

Use the dedicated posterior remapper and three-dimensional initializer with
the exact variable names recorded by that acquisition report. Use
`scripts/prepare_mozart35_initial_condition.py` to expand both Tier C
background states for Tier Z. The commands fail rather than guess provider
field names or overwrite existing artifacts; their `--help` text lists the
required explicit mappings.

Declare the two Tier Z CH4 lineages explicitly:

```bash
conda run -n mpas python scripts/prepare_mozart35_initial_condition.py \
  --source path/inside/data-root/tier-c-cams.nc \
  --output path/inside/data-root/tier-z-cams.nc \
  --report path/inside/data-root/tier-z-cams.audit.json \
  --ch4-lineage cams_inversion

conda run -n mpas python scripts/prepare_mozart35_initial_condition.py \
  --source path/inside/data-root/tier-c-legacy.nc \
  --output path/inside/data-root/tier-z-legacy.nc \
  --report path/inside/data-root/tier-z-legacy.audit.json \
  --ch4-lineage legacy_background
```

Build the closed runtime manifest from the eight prepared artifacts:

```bash
conda run -n mpas python scripts/prepare_global_methane_runtime_manifest.py \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --manifest-id global-methane-v24r2-v6.2-20240701 \
  --partition path/inside/data-root/x1.40962.graph.info.part.8 \
  --nox-inventory path/inside/data-root/miem_inventory.nox.nc \
  --posterior-inventory path/inside/data-root/miem_inventory.ch4.posterior.nc \
  --anthropogenic-inventory path/inside/data-root/miem_inventory.ch4.anthropogenic.nc \
  --tier-c-cams-initial path/inside/data-root/tier-c-cams.nc \
  --tier-c-legacy-initial path/inside/data-root/tier-c-legacy.nc \
  --tier-z-cams-initial path/inside/data-root/tier-z-cams.nc \
  --tier-z-legacy-initial path/inside/data-root/tier-z-legacy.nc \
  --output "$CHEMPAS_EMISSIONS_DATA_ROOT/global-methane-runtime-inputs.json"
```

Run gates in the table order with a clean worktree and one fixed executable:

```bash
conda run -n mpas python scripts/run_global_methane_integration.py \
  --gate C1 \
  --external-inputs "$CHEMPAS_EMISSIONS_DATA_ROOT/global-methane-runtime-inputs.json" \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --executable ./atmosphere_model
```

Repeat with each required gate ID. The runner stages the model, mechanism,
TUV-x configuration/data, MIEM configuration, inventories, initial/restart
state, namelist, streams, and output-field list; it hashes all of them before
launch and invokes the checker after completion.

Render the six paired science bundles only after their reports pass:

```bash
conda run -n mpas python scripts/plot_global_methane.py \
  --report "$CHEMPAS_EMISSIONS_DATA_ROOT/reports/global-methane/COMMIT/c3-report.json" \
  --output-dir "$CHEMPAS_EMISSIONS_DATA_ROOT/figures/global-methane/c3" \
  --dpi 300
```

Open every PNG at full resolution, verify titles, subtitles, units, color
scales, panel completeness, and absence of clipping, then record the visual
inspection against the unchanged hashes:

```bash
conda run -n mpas python scripts/plot_global_methane.py \
  --attest-visual-inspection \
  "$CHEMPAS_EMISSIONS_DATA_ROOT/figures/global-methane/c3/figure-manifest.json"
```

Finally publish only the complete set:

```bash
conda run -n mpas python scripts/publish_global_methane_evidence.py \
  --promotion-root "$CHEMPAS_EMISSIONS_DATA_ROOT/reports/global-methane/COMMIT" \
  --figure-root "$CHEMPAS_EMISSIONS_DATA_ROOT/figures/global-methane" \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --tracked-output docs/chempas/musica/global-methane-evidence \
  --desktop-output "$HOME/Desktop/Global-Tropospheric-Methane"
```

The publisher requires all 14 promotion reports and C3, CA3, CB3, Z3, ZA3,
and ZB3 inspected figure manifests. It rechecks every report, input, history,
configuration, protocol, PNG, and PDF hash and refuses an existing output
directory.

## Verification and Limits

Canonical verification includes Python unit/static tests, all shell/C++
contracts, the independent MOZART-35 box, a clean MUSICA release build,
one-rank/eight-rank MIEM identity, expected runtime failures, and bitwise
MIEM-off ABBA, Chapman–NOx, and lightning baselines.
The exact commands, versions, hashes, and results are recorded in the
[`implementation verification`](global-methane-runs/implementation-verification.md),
with the hash-closed 48-hour solver comparison in the
[`MOZART-35 box report`](global-methane-runs/mozart35-box-qualification.json).

Passing this workflow establishes source coupling, short-timescale process
response, restart behavior, ledger accounting, and reproducibility for these
mechanisms. It does not establish a climatological methane trend, a full
atmospheric lifetime, complete deposition/VOC/sulfur chemistry, stratospheric
methane chemistry, or equivalence to the full 85-species MOZART-4 mechanism.
