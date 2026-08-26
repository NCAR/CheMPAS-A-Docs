# MIEM Emissions Integration

This document is the normative CheMPAS-A workflow for offline emissions through
MUSICA's Model-Independent Emissions Module (MIEM).

> CheMPAS-A does not regrid at runtime. Every production inventory must already
> be conservatively remapped to the exact global MPAS mesh, contain the same
> global cells, and be stored in ascending `indexToCellID` order. Run the
> tracked validator before every launch; the model then performs an independent
> selected-cell geometry check after the first inventory read.

## Scope and data path

MIEM supplies exact-grid column and per-layer mass fluxes from one or more
offline inventories to emission reactions in the active MICM mechanism:

```text
pregridded inventory or inventories (each in global MPAS order)
  -> owned indexToCellID selection on each MPI rank
  -> coalesced rank-local NetCDF hyperslab reads
  -> runtime area/geometry/order validation before MICM mutation
  -> EMIS.<species> MICM rate parameters at each populated layer
  -> MICM coupled and optional reference solves
  -> q<species> MPAS dry mass-mixing-ratio tracers
```

`config_miem_file` is the sole runtime switch. An empty value disables MIEM
construction, inventory I/O, emissions diagnostics, source accounting, and the
`chem MIEM` timer. A nonempty value enables MIEM but does not select the MICM
chemistry mechanism; `config_micm_file` remains a separate required input. One
MIEM mechanism-configuration file may name multiple inventory files and source
maps; CheMPAS still constructs one rank-local aggregate emissions object.

## Build contract

The tested dependency and compiler identities are:

| Component | Tested revision/version |
|---|---|
| CheMPAS-A compiler | GNU Fortran 15.2.0, double precision |
| MUSICA-Fortran | `1403e3d22717bc87f3bf9d0aa591caf039c92bbc` (`0.16.5`) |
| MICM | `bb57684a2047f0e58f30b199366294af879e8597` |
| MIEM | `9fdf14a189262eecb677862d877ab72b06c95e21` |
| MechanismConfiguration | `82c159ae6d74934318ffd6c405a45c2159065b12` |
| TUV-x | `bbf7dd9a144fa0f0294b3779f3f993818638e20c` |

These revisions are a compatibility set, not aliases for current upstream
`main`. In the local 2026-08-16 audit, MUSICA
`a6d34d38f874574b8a0599540f1a12230063ce58` and MIEM
`970e9c20360e25c53b37d5587eebfc81a18336e2` had diverged from the feature
pins above. Audited MUSICA `main` exposes only the full-grid, surface-flux
Fortran MIEM wrapper; it does not expose the selected-cell constructor,
per-layer/group buffers, or exact-grid metadata required here. MICM `main`
`97ac9e5d8aadd345c242722ee8274d71dfe0f73e` contains the tested MICM pin but
is 29 commits newer and has not been qualified with CheMPAS-A. See the
[API revision scope](MUSICA_API.md#supported-revision-scope); do not replace
the tested pins with sibling `main` tips without a forward port and the full
build/runtime qualification.

The tested MUSICA build enables its Fortran interface, MPI, MICM, MIEM, and
TUV-x; it disables shared libraries, tests, CARMA, MIAM, and `fmt`. `fmt` is an
exported dependency only when MUSICA was built with `MUSICA_USE_FMT=ON`.
NetCDF-Fortran is part of the tested TUV-x closure. The package-generated
static link order places `libmiem` before NetCDF-C and selects the platform C++
runtime; CheMPAS-A does not hard-code that runtime.

Run preflight and build with eight-way parallelism:

```bash
eval "$(scripts/check_build_env.sh --export)"
make -j8 "$CHEMPAS_MAKE_TARGET" \
  CORE=atmosphere \
  PIO="$PIO" \
  NETCDF="$NETCDF" \
  NETCDFF="${NETCDFF:-$NETCDF}" \
  PNETCDF="$PNETCDF" \
  PRECISION=double \
  MUSICA=true
```

Preflight requires `musica_micm.mod`, `musica_emissions.mod`, the pinned source
revisions and compiler ABI, and a complete `pkg-config` static closure. It also
links a constructor-level MICM+MIEM probe using only exported package flags.
See the public MVP [build guide](https://github.com/NCAR/CheMPAS-A/wiki/Building)
for the dependency build.

## Exact-grid inventory contract

### UPTEMPO fields, time, and units

Each packaged inventory is NetCDF-4 with:

- dimensions `Time`, `nCells`, and `StrLen=64`;
- `xtime(Time,StrLen)` with `calendar="gregorian"`, nonempty timestamps, and
  strictly increasing values such as `2026-06-22_12:00:00`;
- one or more `float64` source fields with dimensions `(Time,nCells)`;
- source-field units exactly `kg m-2 s-1`;
- finite values with no missing data; values are nonnegative unless the field
  is explicitly declared as signed surface exchange during preparation,
  validation, and runtime staging;
- `indexToCellID(nCells)` stored exactly as `1,2,...,nCells`; and
- the authoritative mesh identity arrays and `chempas-mesh-sha256-v1`
  attributes written by the packaging tool.

The inventory's first and last timestamps must bracket the complete requested
model interval. MIEM linearly interpolates between records. CheMPAS-A supports
the Gregorian calendar only when emissions are enabled. When one MIEM YAML
declares multiple inventories, this contract applies independently to every
file: each must bracket the run and all must report identical exact-grid
metadata for the selected MPAS mesh.

### `chempas-mesh-sha256-v1`

The fingerprint is a canonical SHA-256 stream, normalized into ascending
global-ID order. Every component is length-framed. Text is UTF-8; integers are
signed 64-bit big-endian; floating values are 64-bit big-endian with negative
zero normalized to zero. Units are part of each numeric field's identity. The
stream contains, in order:

1. algorithm tag `chempas-mesh-sha256-v1`;
2. geometry class, `nCells`, normalized `on_a_sphere`, normalized
   `is_periodic`, and `sphere_radius` or its absent marker;
3. `indexToCellID` and `areaCell`; and
4. each present coordinate array in `latCell`, `lonCell`, `xCell`, `yCell`,
   `zCell` order.

A spherical mesh (`on_a_sphere=YES`) must contain `latCell` and `lonCell`. A
planar mesh must contain `xCell`, `yCell`, and `zCell`; all-zero planar
latitude/longitude values are not accepted as a substitute. Optional
coordinates, when present, also enter the fingerprint. The stored algorithm,
digest, and field-manifest attributes must match the inventory contents and the
authoritative MPAS mesh/init file.

## Production preprocessing

Choose a scientifically appropriate conservative remapper for each source
inventory before invoking repository tooling. The packaging command validates,
reorders, converts supported mass-flux units, records remapping provenance, and
writes atomically; it never performs horizontal interpolation.

```bash
python scripts/prepare_miem_inventory.py \
  --mesh /path/to/run_init.nc \
  --source /path/to/already_remapped_inventory.nc \
  --output /path/to/run/miem_inventory.nc \
  --map nox_anth_sum=source_nox \
  --remapping-tool "ESMF_RegridWeightGen 8.x" \
  --remapping-method "first-order conservative"
```

The source must have a global-cell ID variable; positional arrays are rejected.
Supported explicit conversions include `kg m-2 s-1`, `kg m-2 day-1`,
`g m-2 s-1`, and `mg m-2 s-1`. Use `--units NAME=UNITS` only when source
metadata are absent or need an explicit override.

Validation is mandatory and must include the intended model coverage:

```bash
python scripts/validate_miem_inventory.py \
  --mesh /path/to/run_init.nc \
  --inventory /path/to/run/miem_inventory.nc \
  --start-time 2026-06-22_12:00:00 \
  --stop-time 2026-06-23_12:00:00
```

Repeat packaging and validation for every inventory named by the MIEM YAML. Do
not stage or run any inventory if its command fails. In particular, matching
only `nCells` is insufficient: a reordered or geometrically different mesh is
an error even when its cell count is identical.

## Runtime configuration and staging

Paths in both namelist options are resolved from the MPAS process working
directory. MIEM inventory `directory` and `file pattern` entries are likewise
relative to that directory unless absolute paths are used.

```fortran
&chemistry
    config_micm_file = 'miem_nox.yaml'
    config_chem_substeps = 1
/

&emissions
    config_miem_file = 'chem_box_nox.yaml'
    config_miem_net_flux_species = ''
    config_miem_diagnostic_sectors = 'synthetic'
    config_miem_diagnostic_categories = '0'
    config_miem_layered_diagnostics = .true.
    config_miem_max_diagnostic_fields = 256
/
```

Only `config_miem_file` is required. `config_miem_net_flux_species` is an
exact, comma-separated opt-in for species whose positive values are upward
sources and negative values are downward uptake. An empty value preserves the
nonnegative source-only rule for every species. The other four options request
bounded diagnostics and default to no groups, no layered output, and a
256-field cap.
Sector values are comma-separated exact names from the MIEM configuration;
categories are comma-separated nonnegative integers. Unknown, duplicate, or
sanitized-name-colliding sectors and duplicate categories are fatal. With
layered group output, the definitive allocation check is
`species * (sectors + categories) * nVertLevels <= cap` and runs before MPAS
allocates runtime fields.

Stage these inputs together:

- the exact model init/mesh file and the partition matching the MPI rank count;
- every validated inventory under the filename expected by the MIEM YAML;
- the MICM mechanism named by `config_micm_file`;
- the separate MIEM configuration named by `config_miem_file`;
- atmosphere namelist, streams, and requested output fields; and
- normal case-specific tables and auxiliary data.

`EMIS.*` diagnostic names are discovered only from `config_micm_file` because
they are writable MICM rate parameters. `config_miem_file` constructs MIEM and
provides its aggregate output species after all configured sources and
inventories are mapped. Initialization requires an exact one-to-one cross-match
between MIEM species, writable MICM species, and
`EMIS.<species>` parameters. The MIEM YAML may therefore have an empty chemistry
mechanism section; it must not be used as the source of MICM diagnostic names.

The default `vertical injection: surface` is equivalent to a profile with
weight one at level 1 and zero above. A fixed elevated distribution uses a
source-specific profile with exactly one finite, nonnegative weight per MPAS
level and a unit sum, for example:

```yaml
vertical injection: profile
vertical profile: [0.0, 0.25, 0.75, 0.0]
```

The example is schematic and is valid only for a four-level run. The tracked
60-level form is `miem_configs/chem_box_nox_profile.yaml`. Profiles prescribe
vertical allocation; they do not calculate plume rise.

To disable MIEM while retaining chemistry, use:

```fortran
&emissions
    config_miem_file = ''
/
```

## Source conversion and timestep order

For column mass flux `F_s`, normalized level fraction `w_s,k`, and layer
thickness `dz_k = zgrid(k+1,i)-zgrid(k,i)`, MIEM supplies
`F_s,k = w_s,k F_s`. CheMPAS-A writes the MICM molar concentration tendency at
every level:

```text
EMIS.s(k,i) = F_s,k(i) / (dz_k(i) * M_s)    [mol m-3 s-1]
```

The surface-only special case is the original equation
`EMIS.s = F_s / (dz * M_s)` at level 1.

`M_s` is the species molar mass in `kg mol-1`. Dry-air density does not appear:
dividing `kg m-2 s-1` by layer depth already gives `kg m-3 s-1`, and division
by molar mass gives MICM's concentration tendency. Density is needed for
MPAS mixing-ratio/concentration conversion, not this flux conversion.

For a surface source, only level 1 receives flux and every upper-level
`EMIS.*` rate is explicitly zero. For a normalized profile, the declared
levels receive flux and the layer sum closes to the column value. Rates are
installed in the coupled MICM state and, when
`config_chemistry_ref_solve = .true.`, the allocated reference state before
either solve. They remain fixed across `config_chem_substeps`. The fired
chemistry step order is:

1. update photolysis independently;
2. run the selected-cell MIEM object at the chemistry interval start;
3. on the first read, validate the returned global/local dimensions, ordered
   IDs, fingerprint metadata, area, and geometry-required coordinates against
   owned MPAS cells before any MICM mutation;
4. verify finite layer flux, the per-species signed/source-only rule, and column
   closure, then convert and install all `EMIS.*` rates;
5. apply the independent operator-split lightning-NOx source;
6. transfer MPAS state to MICM, solve the coupled state and, when enabled, the
   reference state, then transfer the coupled result back; and
7. publish diagnostics and commit emitted or signed net-exchange mass only
   after successful solves.

## Diagnostics and accounting

An active MIEM run always creates the column total `emis_<species>(Time,nCells)` in
`kg m^{-2} s^{-1}`. Initial fields are exactly zero. After a successful solve,
the diagnostic represents the flux applied during that chemistry interval,
sampled at its interval start; it is not a sample at the output timestamp.

Requested diagnostics use these names and the same mass-flux units:

| Request | Column field | Optional `(nVertLevels,nCells)` field |
|---|---|---|
| Total | `emis_<species>` | `emis_<species>_layer` |
| Sector | `emis_<species>__sector_<label>` | `emis_<species>__sector_<label>_layer` |
| Category | `emis_<species>__category_<id>` | `emis_<species>__category_<id>_layer` |

Sector labels are lowercase alphanumerics with non-alphanumeric runs collapsed
to underscores. The complete field set is validated before any value is
published, so a failed chemistry transaction cannot leave a partial diagnostic
update. When all source categories are requested, their sum closes to the
total; every layered family closes vertically to its matching column field.

At finalize, rank-local successful-step masses are reduced once and rank zero
logs source-only species as:

```text
[MIEM] Total emitted mass for NO: ... kg
[MIEM] Total emitted mass for NO2: ... kg
```

For a species explicitly opted into signed surface exchange, the accumulator
is algebraic and rank zero instead logs, for example:

```text
[MIEM] Net applied surface exchange mass for CH4: ... kg
```

Positive values are net upward input and negative values are net downward
uptake. The applied mass for either contract is:

```text
M_applied(s) = sum_intervals sum_global_cells(
                 emis_s(interval_start,g) * areaCell(g) * dt_interval)
```

For an emissions/exchange-only mechanism, the tracer mass can independently
close the chain, including a negative signed tendency when the initial tracer
mass is sufficient:

```text
M_tracer(s,t) = sum_cells sum_levels(
                  q_s(t,k,g) * rho_dry(t,k,g)
                  * (zgrid(k+1,g)-zgrid(k,g)) * areaCell(g))

M_tracer(s,final) - M_tracer(s,initial) = M_applied(s)
```

This direct NO/NO2 equality is scientifically valid only when there are no
chemical sinks, interconversions, transport losses, or other sources. Reactive
and coexistence cases validate the applied MIEM diagnostic and log accounting,
not an MIEM-only tracer delta.

## Tracked chem-box workflow

The canonical 64-cell init/mesh and 8-rank partition live under
`test_cases/chem_box/miem/assets/`. Verify their manifest before use:

```bash
test_cases/chem_box/miem/regenerate_assets.sh --verify
```

The pinned regeneration environment is
`test_cases/chem_box/miem/asset-environment.yml`; exact MPAS-Tools and init-core
commits are recorded in `assets/PROVENANCE.md`. Regeneration writes to a
separate directory and does not replace tracked assets automatically.

The quickest complete staging and run command is:

```bash
scripts/test_miem_integration.sh \
  --scenario constant_flux \
  --executable ./atmosphere_model \
  --keep-success
```

It verifies the assets, creates and validates a deterministic synthetic
inventory, stages isolated namelist/stream/config inputs, runs MPAS with eight
ranks, audits rank logs, and invokes the throughput checker. The printed
workspace contains `output.nc`, logs, metadata, and the JSON report. Omit
`--keep-success` to retain only the compact report.

The synthetic generator is for tests, not a production inventory. It copies
the authoritative mesh identity and writes deterministic `zero`, `constant`,
or `cell-time-signature` NOx fields:

```bash
python test_cases/chem_box/miem/generate_fixture.py \
  --pattern cell-time-signature \
  --output /path/to/run/miem_inventory.nc \
  --verify-sha256
```

## R0-R6 regression matrix

Definitions, exact timesteps, tolerances, overrides, and expected assertions
are tracked in `test_cases/chem_box/miem/scenarios.yaml`:

| ID | Scenario | Primary contract |
|---|---|---|
| R0 | `disabled` | No MIEM object, I/O, timer, or emissions diagnostics |
| R1 | `zero_flux` | Enabled zero diagnostics/budgets and unchanged tracers |
| R2 | `constant_flux` | Unit conversion and inventory-to-tracer mass closure |
| R3 | `cell_time_signature` | Global-ID mapping and endpoint/midpoint interpolation |
| R4 | `substeps_restart` | Substep sampling and continuous/restart equivalence |
| R5 | `lightning_coexistence` | Separate MIEM accounting with lightning NOx active |
| R6 | `layered_diagnostics` | Normalized vertical profile and bounded sector/category diagnostic closure |

Run the complete matrix and the focused 1-rank/8-rank mapping comparison:

```bash
scripts/test_miem_integration.sh \
  --scenario all \
  --executable ./atmosphere_model
```

The checker can also be called directly when retained artifacts and
`run-metadata.json` are available:

```bash
python scripts/check_miem_throughput.py \
  --scenario constant_flux \
  --history /path/to/run/output.nc \
  --inventory /path/to/run/miem_inventory.nc \
  --mesh /path/to/run/chem_box_init.nc \
  --log /path/to/run/log.atmosphere.0000.out \
  --metadata /path/to/run/run-metadata.json \
  --report /path/to/report.json
```

Reports conform to
`test_cases/chem_box/miem/throughput-report.schema.json`. They record file and
configuration hashes, dependency/compiler/rank provenance, extrema and errors,
source/log/tracer masses, resolved tolerances, and pass/fail assertions. They
also record inventory/history bytes and the `chem MIEM` timer. The historical
throughput fields retain per-rank and aggregate effective-rate estimates for
R0-R6 continuity, but they do not infer selected NetCDF payload and are not a
scalability gate. The production-mesh reports described below provide the
rank-local payload, state, hyperslab, time, and RSS evidence.

## Verified emissions figures

The tracked visualization bundle is generated only from passing eight-rank
R2, R3, and R6 throughput evidence. Those three scenarios are source-only, so
the plotter checks the history/report hash, exact grid order, physical units,
finite nonnegative diagnostics, initial zero fields, layer/group closure, and
final diagnostic-to-tracer mass closure before writing either image format.

```{figure} ../../_static/miem_emissions_spatial.png
:alt: Two exact-grid maps showing the synthetic NO and NO2 emissions fluxes.
:name: miem-emissions-spatial

Final R3 exact-grid cell/time-signature diagnostics. The nonuniform cell
pattern validates global-ID placement, and the panels retain the configured
9:1 NO:NO2 mass split.
```

```{figure} ../../_static/miem_emissions_vertical.png
:alt: Vertical allocation curves and grouped NO and NO2 emissions bars.
:name: miem-emissions-vertical

Final R6 layered and disaggregated diagnostics. The elevated profile allocates
25% and 75% of the column source to the two active layers; each requested
sector and category family closes to the total.
```

```{figure} ../../_static/miem_emissions_budget.png
:alt: Thirty-minute NO and NO2 source-rate and cumulative-mass closure plots.
:name: miem-emissions-budget

All 31 frames of the extended R2 emissions-only run. Across 600 chemistry
intervals, integrated output diagnostics, finalize logs, and dry tracer mass
close for NO and NO2; the figure reports the independently calculated final
relative diagnostic/tracer errors.
```

The accompanying
[figure manifest](../results/miem-emissions-figure-manifest.json) records all
input and output SHA-256 values, the selected frames, the 30-minute run
configuration, and closure errors. See the
[visualization guide](../guides/VISUALIZE.md) for exact reproduction commands,
the plotting protocol, the synthetic-versus-production data boundary, and the
longer-run decision.

### Global coupled A1 figures

The Phase 9D bundle uses the passing 24-hour x1.40962 A1 report, not the
synthetic chem-box cases. `plot_global_miem_science.py` verifies the exact
external-input manifest and the full-file hashes of the selected final enabled
and matched-control histories before reading spatial fields. Time-series panels
use all 25 hourly diagnostics already closed by the A1 checker.

```{figure} global-runs/figures/stage9d_global_emissions_response.png
:alt: Global NO and NO2 surface emissions maps above matched-control column-response maps.
:name: stage9d-global-emissions-response

CAMS-GLOB-ANT v6.2 surface flux at the final accepted diagnostic frame and the
24-hour enabled-minus-control NO and NO2 column response. Dense x1.40962 cells
are rasterized in the vector PDF; colorbars retain explicit physical units.
```

```{figure} global-runs/figures/stage9d_noy_budget.png
:alt: Global emissions rates, reactive nitrogen closure, burdens, and sector diagnostics.
:name: stage9d-noy-budget

All hourly source diagnostics, the integrated emitted-N versus matched-control
NOy response, reactive NO/NO2 partitioning, and retained sector totals. The
final source/response residual is `1.435e-11` relative.
```

```{figure} global-runs/figures/stage9d_diurnal_structure.png
:alt: Photolysis day-night cycles, vertical NOy structure, and hemispheric burdens.
:name: stage9d-diurnal-structure

TUV-x day/night cycles at four geographic anchors, global photolysis coverage,
resolved 26-level NOy structure, and hemispheric evolution across the full
diurnal trajectory.
```

The portable
[A1 figure manifest](global-runs/stage9d-figure-manifest.json) records the A1
report, external manifest, inventory, selected histories, code, style, figures,
software commits, executable hash, and scientific-interpretation boundary.
These panels establish coupled software/process behavior. The meteorology is
date matched, but the Chapman-NOx background is idealized and not chemically
spun up; the displayed first-day concentrations are not production air-quality
predictions. Exact reproduction commands are in the
[visualization guide](../guides/VISUALIZE.md).

## Current `develop` capability status

As of the 2026-08-16 documentation audit, the surrounding CheMPAS chemistry
features have the following status. This table distinguishes implemented
software from science experiments that have not been promoted.

| Capability | Current status and MIEM relationship |
|---|---|
| Global MVP | The [MVP release candidate](../mvp/MVP_PRE_RELEASE.md) is complete: its 24-hour x1.40962 No Surface Emissions, Anthropogenic Emissions, and Anthropogenic + Fire Emissions attribution uses independent CAMS anthropogenic and FINN fire inventories with reduced chemistry and passed the repository regression suite. It is a process demonstration, not a production forecast. |
| Multiple inventories | Implemented and tested through one `config_miem_file`. The MVP combines the separate CAMS and FINN files in `miem_configs/global_mvp_cams_finn.yaml`; `miem_configs/two_inventory_nox_ch4.yaml` also exercises independent NOx and CH4 files. Every inventory is sampled independently, must carry the same exact-grid identity, and contributes through MIEM's normal category/hierarchy aggregation. |
| Signed net flux | Implemented as an exact-species opt-in. Positive exchange and negative uptake are preserved through layer rates, diagnostics, and algebraic mass accounting; all non-opted species remain source-only. |
| Prescribed upper O3 | The [spatial monthly O3 provider](../mvp/STAGE1_PRESCRIBED_O3.md) is implemented and qualified, but it is not an MIEM source. It extends the TUV-x column strictly above the model top and never modifies prognostic `qO3`. |
| Chemistry VMR output | [Complete and revalidated](../CHEM_TRACER_OUTPUT_UNITS_PLAN.md). Optional `vmr_<species>` fields are history-only diagnostics; transported and restarted `q<species>` fields remain dry-air mass mixing ratios. This output conversion does not change MIEM flux units. |
| MOZART-35 / global methane | The generated Tier Z mechanism, host bindings, MIEM NOx+CH4 software path, ledgers, and independent box qualification are implemented. The [global methane workflow](GLOBAL_TROPOSPHERIC_METHANE.md) is not science-promoted: CAMS inversion data access and the recorded disk-capacity requirement still block the required global gates. |

## Lightning coexistence

MIEM and `mpas_lightning_nox.F` are independent sources. Enabling both does not
replace, deduplicate, or reconcile them. `emis_NO` and `emis_NO2` plus MIEM's
final mass logs contain only MIEM flux; lightning modifies the NO tracer
separately. If an offline inventory already represents lightning NOx, enabling
the operator-split lightning source can double count it. R5 enables both
intentionally to prove coexistence and does not interpret total tracer change
as an MIEM-only budget.

## Scalability evidence and current boundaries

Each rank constructs MIEM with global `nCells`, the actual MPAS level count,
and only its ordered owned global IDs. UPTEMPO/ECCAD readers sort a temporary
index, coalesce consecutive IDs, issue `nc_get_vara` calls for those runs, and
scatter back into host order. Flux buffers, two cached time brackets, and exact
grid metadata therefore scale with owned cells; MIEM performs no MPI calls.

The reproducible benchmark command is:

```bash
scripts/benchmark_miem_scalability.sh --case all --warm-steps 12
```

It expects external production init/mesh and partition files under
`$HOME/Data/CheMPAS` by default, creates a temporary deterministic exact-grid
NO/NO2 inventory, and runs full-grid and selected-cell modes on eight ranks.
The committed [regional and global reports](benchmarks/README.md) cover the
28,080-cell planar supercell mesh and 40,962-cell spherical x1.40962 mesh. In
both reports, selected aggregate NetCDF payload and modeled persistent state
are exactly `1/8` of replicated totals, every owned-cell flux stream is
bitwise identical, and no selected rank reports global-sized flux buffers.
Initialization/warm-step time and peak RSS are recorded but are not portable
performance thresholds.

Current scientific boundaries remain explicit: inventories must be externally
remapped onto the exact MPAS grid; runtime native regridding is unsupported;
emissions use Gregorian timestamps; vertical profiles are fixed normalized
fractions rather than meteorology-dependent plume rise; and each rank performs
independent serial NetCDF hyperslab reads rather than collective parallel I/O.
The full-grid MUSICA constructor remains only for backward compatibility and
the bitwise reference/benchmark path; CheMPAS runtime uses selected cells.

## Disabled baselines and checkpoint provenance

`test_cases/miem_disabled_baselines.json` pins ABBA, Chapman-NOx, and
lightning-NOx outputs from pre-emissions CheMPAS-A source `4eb4e677...` rebuilt
against the same pinned MUSICA/MIEM stack as the Phase 9 candidate. E0 is valid
only with the recorded compiler, double precision, PIO/NetCDF stack,
configuration and input hashes, eight-rank commands, and canonical field-hash
policy. A different dependency, compiler, precision, input, or field policy
cannot claim E0. Run the comparison with:

```bash
scripts/test_miem_disabled_baselines.sh /path/to/clean/build --case all
```

The immutable `test_cases/miem_disabled_baselines.phase0.json` archive retains
the original Phase 0 dependency provenance. The harness verifies the archive,
retained preimplementation executable, active baseline containers and logs,
and exact equality of all 195 canonical scientific field hashes between the
historical and same-stack captures. NetCDF container-hash changes do not stand
in for scientific-field differences.

## Phase 9E release evidence

The authoritative compact release record is
[`stage9e-release-manifest.json`](global-runs/stage9e-release-manifest.json). It
requires all of the following:

- a G3 run created from an empty staging root using tracked orchestration and
  manifest-resolved external inputs;
- a decisive A1 recheck with all 47 assertions and canonical equality to the
  accepted Stage 9D report except volatile free-disk telemetry;
- the versioned Phase 9 figure manifest and exact plot hashes;
- all nine R0-R6 reports, all three strict same-stack E0 reports, selected/full
  and one/eight-rank mapping, and six expected runtime failure contracts; and
- exact compiler, executable, dependency, inventory, partition, command,
  report, external-retention, and tracked-artifact identities.

Large NetCDF inputs, histories, restarts, captured baselines, and run trees
remain under `CHEMPAS_EMISSIONS_DATA_ROOT` with no automatic cleanup. The gate
validates software coupling, applied-source throughput, reactive-N accounting,
restart/control behavior, performance telemetry, and reproducibility. The
date-matched meteorology and science-grade CAMS inventory support that coupled
process experiment; the idealized, unspun Chapman-NOx initial composition does
not make its first-day concentrations production air-quality estimates.

Implementation follows a verify-commit-push checkpoint after every completed
phase, stage, or milestone. Required phase commit messages are listed in
`docs/chempas/mvp/PLAN_EMISSIONS.md`; pushed SHAs, build roots, report roots, and verification
results are recorded in `docs/chempas/MIEM_IMPLEMENTATION_LOG.md`. No phase
advances until its checkpoint SHA is present on `origin/develop_emissions`.

## Related documentation

- [Global tropospheric NOx ladder](GLOBAL_TROPOSPHERIC_NOX.md)
- [Global tropospheric methane and MOZART-35](GLOBAL_TROPOSPHERIC_METHANE.md)
- [MUSICA integration](MUSICA_INTEGRATION.md)
- [MUSICA API reference](MUSICA_API.md)
- [Architecture](../architecture/ARCHITECTURE.md)
- [Build guide](https://github.com/NCAR/CheMPAS-A/wiki/Building)
- [Getting started](https://github.com/NCAR/CheMPAS-A/wiki/Getting-Started)
- [Global chemistry and emissions](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions)
