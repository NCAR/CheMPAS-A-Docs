# MVP Stage 0 Data and Interface Freeze

**Recorded:** 2026-08-15 (America/Denver)
**Result:** PASS

Stage 0 freezes the inputs, transformations, runtime interface, resource
envelopes, and pre-change regression baseline for `PLAN_MVP.md`. The compact
machine record is [`stage0-audit.json`](stage0-audit.json). Large provider
files and generated reports remain under `CHEMPAS_EMISSIONS_DATA_ROOT`.

## Frozen Sources

The authoritative manifest is
[`external-inputs.json`](../../_downloads/mvp/external-inputs.json),
validated against
[`external-inputs.schema.json`](../../_downloads/mvp/external-inputs.schema.json).
Every declared byte size and SHA-256 passed on the exact files used here.

| Purpose | Frozen source | Selection |
|---|---|---|
| Upper O3 | MERRA-2 M2IMNPASM v5.12.4, DOI `10.5067/2E096JV59PK7` | Twelve 2024 monthly means of O3 and H at 3–0.1 hPa |
| Anthropogenic CO | CAMS-GLOB-ANT v6.2, DOI `10.24380/eets-qd81` | July and August 2024 monthly CO, all provider sectors and `sum` |
| Fire CO/NOx | FINNv2.5.1 MODIS+VIIRS NRT | 2024-07-01 and 2024-07-02 explicit CO, NO, and NO2 |
| Runtime grid | MPAS x1.40962 | Exact 40,962-cell mesh and eight-rank partition |
| Initial state | NOAA-GFS-derived expanded Tier C state | 2024-07-01 00:00 UTC, 26 levels, 45 km model top |
| Accepted NOx | CAMS-GLOB-ANT v6.2 exact-grid package | Existing explicit NO and NO2 inventory |

MERRA-2 acquisition used bounded authenticated DAP2 reads when available and
an authenticated transient-granule fallback otherwise. Complete fallback
granules were deleted immediately after the selected O3/H subset was written
and verified. `pydap` 3.5.10 is an acquisition-only dependency; it is not a
model runtime dependency.

The CAMS audit independently reconstructed the provider `sum` from all eleven
sectors. The largest global relative discrepancy was
`2.3650169792271097e-09`, below the frozen `5e-6` tolerance. The raw source
retains `awb`; exact-grid harmonized packages omit it.

## FINN Interpretation

FINN gas fields are provider totals in mol species per day. The two frozen
files contain 65,462 and 63,419 records. The audit maps provider `CO`, `NO`,
and `NO2` directly and does not use `NOXasNO`.

The provider `DAY` is a fire-local calendar date, not a UTC interval. Because
the text product does not retain subdaily event timing, the MVP converts each
daily total to a mean rate by dividing by 86,400 seconds and uses nearest
records anchored at 12:00 UTC. This is a declared timing approximation with a
longitude-dependent displacement of at most 12 hours. It must not be labeled
as provider UTC-day semantics.

MIEM rejects extrapolation outside an inventory's declared time range. The
runtime package therefore duplicates the first daily field at 2024-07-01
00:00 UTC as an explicit coverage guard for the pre-noon interval. The two
scientific records remain anchored at noon, and nearest interpolation still
switches from the first to second daily field at their midnight midpoint
(with an exact midpoint selecting the earlier record). The guard is metadata-
labeled and does not introduce a third provider observation.

The FINNv2.5.1 NRT text has a reproducible formatting defect: `BMASS` and
`FRP` occupy one comma-delimited field. The acquisition parser accepts only
the observed 25-field row, requires exactly two whitespace-separated values
at that position, reconstructs the declared 26 fields, and otherwise fails.

## Source Separation

Attribution members use one overlap policy throughout:

- No Surface Emissions withholds the harmonized CAMS and FINN target sources;
- Anthropogenic Emissions applies CAMS NO, NO2, and CO without the CAMS `awb` sector;
- Anthropogenic + Fire Emissions applies the same CAMS package plus FINN CO, NO, and NO2;
- all fire emissions use surface injection for the MVP.

Thus `B - A` is the anthropogenic source contribution and `C - B` is the fire
source contribution. The words *enabled*, *disabled*, *forcing*, and an
unqualified *control* are not public experiment labels.

## Prescribed-Field Interface

[`prescribed-field-contract.json`](../../_downloads/mvp/prescribed-field-contract.json)
is the normative NetCDF interface description. The exact-grid package has 12
monthly records, 40,962 cells, eleven 5 km upper layers, and edges from 45 to
100 km. It carries exact `indexToCellID` values and the
`chempas-mesh-sha256-v1` fingerprint.

Preparation conservatively remaps air and O3 columns horizontally, then
redistributes source pressure-layer O3 columns onto the fixed height layers.
Only source fractions strictly above 45 km enter the prescribed column.
Uncovered source-top fractions use the frozen AFGL mid-latitude-summer O3
tail; US Standard Atmosphere 1976 supplies structural temperature and air
number density. Both the stored layer column and consistent layer number
density are retained so vertical closure can be checked independently.

Monthly values are means over declared Gregorian bounds and are anchored at
the bound midpoints. Runtime interpolation is linear and cyclic, including
December-to-January wrap and leap-year month lengths. Each rank caches only
the two active records for owned cells. Missing metadata, a mesh mismatch,
invalid coordinates or units, nonfinite/negative O3, or incomplete
configuration is fatal; the legacy static CSV path remains a separate mode.

## Resources and Retention

[`resource-forecast.json`](../../_downloads/mvp/resource-forecast.json)
uses a 180 MiB history-frame envelope, 1,000 MiB restart envelope, 1.25 safety
factor, 4.5 GiB peak-memory envelope, and a 20 GiB disk reserve. M3 is the
largest gate at a 6,370,099,200-byte allowed output envelope. At the Stage 0
audit, 29,519,974,400 bytes were available, exceeding the required
27,844,935,680 bytes.

Gates run sequentially. After a gate is checked and its compact reports and
selected evidence are hash-recorded, replaceable histories, restarts, logs,
and staged executables are removed before the next storage-limited gate.

## Pre-MVP Regression Baseline

The clean build used commit `7449fd0f0e91259814cb9450034303bba38af0de`
and the pinned dependency closure recorded in `stage0-audit.json`. Its
14,100,160-byte `atmosphere_model` has SHA-256
`e95e93b15c0a1f5ca71dbbc32f070a9c0f0d734b1aadefa89ea44a0b4c2905db`.

Before runtime implementation:

- build-environment preflight passed;
- Python and shell static checks passed;
- all 230 existing Python unit tests passed;
- all three 16-point JPL Troe matrices passed;
- every existing MUSICA emission/mechanism contract passed; and
- a clean double-precision, MUSICA-enabled atmosphere build passed.

Stage 0 therefore promotes with no runtime code required to infer provider
metadata or scientific policy.

The runtime manifest now also registers the three hash-frozen products
qualified in Stages 1 and 2: the exact-grid monthly upper-O3 climatology, the
harmonized non-fire CAMS NO/NO2/CO package, and the FINN fire NO/NO2/CO
package. This raises the manifest artifact count from eight acquired/baseline
inputs to eleven total inputs without changing the frozen source decisions.
