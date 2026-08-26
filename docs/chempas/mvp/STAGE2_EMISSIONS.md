# MVP Stage 2: CO and Source Inventories

Stage 2 adds a host-supplied CO entry point to Tier C and prepares two
independent exact-grid source groups: harmonized non-fire CAMS and FINN fire.
It does not change the reviewed Tier C gas-phase reactions.

## Mechanism Contract

The normal and strict Tier C snapshots now expose exactly `EMIS.NO`,
`EMIS.NO2`, and `EMIS.CO`. Their non-emission reactions, species, phases, and
photolysis mappings remain identical to the accepted predecessor mechanism.
The Tier C plus methane-source snapshots likewise retain their existing
chemistry and add CO beside NO, NO2, and CH4.

Two independent checks cover the new entry point:

- a Fortran host-binding test verifies discovery, exact-zero assignment,
  positive flux conversion, configured solver tolerance, and explicit
  rejection of negative CO source flux; and
- an actual MICM box integrates a known surface flux through a 150 m layer and
  independently closes CO concentration, CO mass, and elemental carbon in
  both normal and strict snapshots.

The accepted pre-CO F0 report and current zero-CO F0 report have bitwise-equal
box cases, column results, and Troe matrix. Their only rate-parameter-set
difference is the added zero-valued `EMIS.CO` entry.

## Harmonized CAMS Source

[`prepare_mvp_emissions.py`](../../_downloads/mvp/prepare_mvp_emissions.py) reuses
the qualified CAMS 0.1-degree-to-x1.40962 conservative weights. It preserves
the accepted explicit NO and NO2 sector fields, conservatively remaps every
native CO sector, and constructs audited no-`awb` sums. Individual retained
sector fields remain in the package for source diagnostics; chemistry uses
only the audited explicit NO, NO2, and CO sums.

The raw provider `sum` is reconstructed from all CO sectors before `awb` is
withheld. Maximum provider-sector closure is `2.365017092438672e-09` relative.
All 6,480,000 source cells and 40,962 destination cells are represented; the
maximum source-area relative error in the weight audit is
`2.0231421346296964e-12`. July harmonized global rates are 2,144.058142 kg/s
NO, 238.228682 kg/s NO2, and 14,464.758823 kg/s CO. The separately recorded
withheld July `awb` amounts are 49.758986, 5.528776, and 2,299.437836 kg/s,
respectively.

## FINN Fire Source

The FINNv2.5.1 preparation reads the provider's explicit CO, NO, and NO2
mol-species/day fields and ignores `NOXasNO`. Each fire-point total is assigned
to its nearest x1.40962 cell center, then divided by 86,400 seconds and the
authoritative cell area. This point allocation conserves the global provider
amount by construction and does not imply plume rise; all MVP fire sources
enter the surface layer.

The July 1 and July 2 records occupy 2,738 and 2,868 destination cells. Their
maximum point-to-cell distances are 70.029 and 69.880 km. Every species amount
closes at or below `2.55e-16` relative. The provider-local-date timing remains
an explicitly approximate nearest-record treatment with noon UTC anchors and
up to 12 hours of longitude-dependent displacement.

Because MIEM correctly rejects time extrapolation, the package includes one
metadata-labeled coverage guard at 2024-07-01 00:00 UTC that duplicates the
first daily field. It covers the simulation's pre-noon interval without
inventing another observation or changing the noon-to-noon nearest switch.

## Runtime Separation and Audit

[`global_mvp_cams.yaml`](../../_downloads/mvp/global_mvp_cams.yaml) applies
only the harmonized CAMS source group. The two-inventory
[`global_mvp_cams_finn.yaml`](../../_downloads/mvp/global_mvp_cams_finn.yaml)
adds FINN as a separate fire source with independent nearest interpolation.
Neither configuration references a CAMS `awb` field.

At 2024-07-01 12:00 UTC, the independent package reconstruction gives:

| Species | CAMS (kg/s) | FINN (kg/s) | Sum (kg/s) |
|---|---:|---:|---:|
| NO | 2,143.800757 | 289.884773 | 2,433.685530 |
| NO2 | 238.200084 | 679.494713 | 917.694797 |
| CO | 14,460.729696 | 19,396.537956 | 33,857.267652 |

An actual MIEM selected-cell test independently reads the source files and
matches CAMS-only and CAMS-plus-FINN fluxes for NO, NO2, and CO at simulation
start, the first noon anchor, the midnight nearest-record tie, and one hour
after midnight. The same audit closes the combined nitrogen and carbon rates.

## Reproduction

With `CHEMPAS_EMISSIONS_DATA_ROOT` set to the Stage 0 data root:

```bash
conda run -n mpas python scripts/prepare_mvp_emissions.py all \
  --manifest test_cases/global_mvp/external-inputs.json
conda run -n mpas bash scripts/test_mvp_co_source.sh
conda run -n mpas bash scripts/test_musica_emission_contracts.sh .
conda run -n mpas bash scripts/test_mvp_multiple_inventories.sh \
  "$CHEMPAS_EMISSIONS_DATA_ROOT"
conda run -n mpas python -m unittest tests.test_prepare_mvp_emissions
```

Large native inputs, exact-grid NetCDF files, weights, and full reports remain
outside Git. [`stage2-emissions-audit.json`](stage2-emissions-audit.json)
records their byte sizes and SHA-256 identifiers.
