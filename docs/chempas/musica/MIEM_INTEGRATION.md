# MIEM Emissions Integration

This document is the normative CheMPAS-A workflow for offline emissions through
MUSICA's Model-Independent Emissions Module (MIEM).

> CheMPAS-A does not regrid at runtime. Every production inventory must already
> be conservatively remapped to the exact global MPAS mesh, contain the same
> global cells, and be stored in ascending `indexToCellID` order. Validate each
> inventory against that mesh before every launch; the model then performs an
> independent selected-cell geometry check after the first inventory read.

The inventory packaging and validation scripts, the chem-box test assets and
harness, the plotting script, the scalability benchmark, and the `miem_configs/`
files named on this page are maintained in the CheMPAS-A development
repository. They are not part of the
[v2026.08.01 release](https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01).
Without them, prepare inventories by following the manual preparation contract
on the wiki
[Data and Provenance](https://github.com/NCAR/CheMPAS-A/wiki/Data-and-Provenance)
page together with the exact-grid inventory contract below.

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

The climatological upper-column O3 that extends the TUV-x photolysis column is
not an MIEM source: it applies strictly above the model top and never modifies
prognostic `qO3`.

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
`main`. MUSICA and MIEM `main` have diverged from the feature pins above:
MUSICA `main` exposes only the full-grid, surface-flux Fortran MIEM wrapper;
it does not expose the selected-cell constructor, per-layer/group buffers, or
exact-grid metadata required here. MICM `main` contains the tested MICM pin
but is newer and has not been tested with CheMPAS-A. The
[MUSICA API reference](MUSICA_API.md) lists the supported revision scope. Do
not replace the tested pins with upstream `main` tips without a forward port
and a full rebuild and retest.

The tested MUSICA build enables its Fortran interface, MPI, MICM, MIEM, and
TUV-x and disables CARMA, MIAM, and `fmt`. Its libraries are static because
`MUSICA_BUILD_SHARED_LIBS` defaults to `OFF`. The documented configure step
also passes `-DBUILD_SHARED_LIBS=OFF` and `-DBUILD_TESTING=OFF`, but neither is
a MUSICA option at the pinned revision. MUSICA's own tests are controlled by
`MUSICA_ENABLE_TESTS`, which defaults to `ON`, so that step still builds them.
`fmt` is an exported dependency only when MUSICA was built with
`MUSICA_USE_FMT=ON`. NetCDF-Fortran is part of the tested TUV-x closure. The
package-generated static link order places `libmiem` before NetCDF-C and
selects the platform C++ runtime; CheMPAS-A does not hard-code that runtime.

Install the pinned MUSICA package and run the `pkg-config` metadata checks in
the [build guide](../../users-guide/03-building.md) first. Those checks compare
the MUSICA, MICM, MIEM, MechanismConfiguration, and TUV-x revisions and report
the Fortran compiler that built the package. `CHEMPAS_MAKE_TARGET` and the
dependency paths are set in the guide's platform sections. Then build with
eight-way parallelism:

```bash
make -j8 "$CHEMPAS_MAKE_TARGET" \
  CORE=atmosphere \
  PIO="$PIO" \
  NETCDF="$NETCDF" \
  NETCDFF="${NETCDFF:-$NETCDF}" \
  PNETCDF="$PNETCDF" \
  PRECISION=double \
  MUSICA=true
```

With `MUSICA=true`, the Makefile requires the `musica-fortran` package at
version `0.16.5` with the pinned MUSICA source revision, the pinned MIEM
revision, and MIEM enabled. It does not check the MICM, MechanismConfiguration,
or TUV-x revisions; the `pkg-config` checks above cover those. It then compiles
and links a constructor-level MICM+MIEM probe against `musica_micm` and
`musica_emissions` using only the exported package flags. A missing Fortran
module, an incomplete static closure, or a compiler ABI mismatch fails at this
probe. The wiki [build guide](https://github.com/NCAR/CheMPAS-A/wiki/Building)
covers the dependency build.

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
  attributes written when the inventory is packaged.

The inventory's first and last timestamps must bracket the complete requested
model interval. Each source in the MIEM configuration selects how MIEM samples
between records with `temporal interpolation`: `linear` blends the two
bracketing records and `nearest` takes the nearer one. In the wiki's global
example, the CAMS source uses `linear` and the FINN fire source uses `nearest`.
CheMPAS-A supports the Gregorian calendar only when emissions are enabled.
When one MIEM YAML declares multiple inventories, this contract applies
independently to every file: each must bracket the run and all must report
identical exact-grid metadata for the selected MPAS mesh.

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
coordinates, when present, also enter the fingerprint.

The development repository's packaging and validation tools recompute the
digest from the inventory and from the authoritative MPAS mesh/init file, and
reject an inventory whose stored digest or field manifest does not match. The
model does not recompute the digest. On the first inventory read it requires
the algorithm string `chempas-mesh-sha256-v1`, a 64-character digest, and a
non-empty field manifest. It then compares the global cell count, geometry
class, `on_a_sphere`, `is_periodic`, `sphere_radius` when present, and each
owned cell's `indexToCellID`, `areaCell`, and coordinates, including their
units, against the running mesh. The coordinates compared are those the
geometry requires plus any optional ones the inventory carries.

## Production preprocessing

The commands in this section run `scripts/prepare_miem_inventory.py` and
`scripts/validate_miem_inventory.py` from the CheMPAS-A development repository;
neither script is in the v2026.08.01 release. Without them, follow the wiki
[Data and Provenance](https://github.com/NCAR/CheMPAS-A/wiki/Data-and-Provenance)
page, which gives the remapping, packaging, and mesh-identity requirements for
the global example's inventories.

Choose a scientifically appropriate conservative remapper for each source
inventory before packaging. The packaging command validates, reorders, converts
supported mass-flux units, records remapping provenance, and writes atomically;
it never performs horizontal interpolation.

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

The two file names are the development repository's chem-box configurations,
`micm_configs/miem_nox.yaml` and `miem_configs/chem_box_nox.yaml`; the latter
has one source with sector `synthetic` and category `0`. The wiki's
Anthropogenic + Fire Emissions scenario instead sets
`global_cams_tropo_ch4nox.yaml` and `global_mvp_cams_finn.yaml`, with sectors
`cams_harmonized_no_awb,finn_fire` and categories `0,100`.

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

The
[global chemistry and emissions example](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions)
publishes its MIEM configurations in the wiki's `examples/global-emissions/`
directory. `global_mvp_cams.yaml` reads one harmonized CAMS-GLOB-ANT
anthropogenic inventory, and `global_mvp_cams_finn.yaml` combines that
inventory with a separate FINNv2.5.1 fire inventory. Each inventory is sampled
independently and contributes through MIEM's normal category/hierarchy
aggregation.

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

The example is schematic and is valid only for a four-level run. The
development repository's 60-level chem-box form is
`miem_configs/chem_box_nox_profile.yaml`. Profiles prescribe vertical
allocation; they do not calculate plume rise.

To disable MIEM while retaining chemistry, use:

```fortran
&emissions
    config_miem_file = ''
/
```

With MIEM disabled, the ABBA, Chapman-NOx, and lightning-NOx cases produce the
same scientific output fields as CheMPAS-A before emissions support was added,
given the same compiler, dependencies, and inputs.

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
Optional `vmr_<species>` chemistry output does not change these units;
transported and restart `q<species>` fields remain dry-air mass mixing ratios.

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

The chem-box assets, scenario definitions, harness, and checker in this and
the next two sections are in the CheMPAS-A development repository, not the
v2026.08.01 release.

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

## Chem-box test scenarios

Definitions, exact timesteps, tolerances, overrides, and expected assertions
are tracked in `test_cases/chem_box/miem/scenarios.yaml`:

| Scenario | Primary contract |
|---|---|
| `disabled` | No MIEM object, I/O, timer, or emissions diagnostics |
| `zero_flux` | Enabled zero diagnostics/budgets and unchanged tracers |
| `constant_flux` | Unit conversion and inventory-to-tracer mass closure |
| `cell_time_signature` | Global-ID mapping and endpoint/midpoint interpolation |
| `substeps_restart` | Substep sampling and continuous/restart equivalence |
| `lightning_coexistence` | Separate MIEM accounting with lightning NOx active |
| `layered_diagnostics` | Normalized vertical profile and bounded sector/category diagnostic closure |

Run every scenario and the 1-rank/8-rank mapping comparison:

```bash
scripts/test_miem_integration.sh \
  --scenario all \
  --executable ./atmosphere_model
```

The checker can also be called directly when retained run outputs and
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
also record inventory/history bytes and the `chem MIEM` timer. Their per-rank
and aggregate effective-rate estimates do not measure the selected NetCDF
payload; use the scalability benchmark below for rank-local I/O and memory
measurements.

## Chem-box emissions figures

The development repository's `scripts/plot_miem_emissions.py` draws these
figures from passing eight-rank `cell_time_signature`, `layered_diagnostics`,
and `constant_flux` runs. Those scenarios are source-only, so before writing
the PNG and PDF files the plotter checks the history/report hash, exact grid
order, physical units, finite nonnegative diagnostics, initial zero fields,
layer/group closure, and final diagnostic-to-tracer mass closure.

```{figure} ../../_static/miem_emissions_spatial.png
:alt: Two exact-grid maps showing the synthetic NO and NO2 emissions fluxes.
:name: miem-emissions-spatial

Final exact-grid diagnostics from the `cell_time_signature` scenario. The
nonuniform cell pattern shows global-ID placement, and the panels retain the
configured 9:1 NO:NO2 mass split.
```

```{figure} ../../_static/miem_emissions_vertical.png
:alt: Vertical allocation curves and grouped NO and NO2 emissions bars.
:name: miem-emissions-vertical

Final layered and disaggregated diagnostics from the `layered_diagnostics`
scenario. The elevated profile allocates 25% and 75% of the column source to
the two active layers; each requested sector and category family closes to the
total.
```

```{figure} ../../_static/miem_emissions_budget.png
:alt: Thirty-minute NO and NO2 source-rate and cumulative-mass closure plots.
:name: miem-emissions-budget

All 31 output frames of a 30-minute `constant_flux` emissions-only run. Across
600 chemistry intervals, integrated output diagnostics, finalize logs, and dry
tracer mass close for NO and NO2; the figure reports the independently
calculated final relative diagnostic/tracer errors.
```

The [visualization guide](../guides/VISUALIZE.md) gives the commands that
reproduce these figures and describes the boundary between synthetic test data
and production inventories.

## Lightning coexistence

MIEM and `mpas_lightning_nox.F` are independent sources. Enabling both does not
replace, deduplicate, or reconcile them. `emis_NO` and `emis_NO2` plus MIEM's
final mass logs contain only MIEM flux; lightning modifies the NO tracer
separately. If an offline inventory already represents lightning NOx, enabling
the operator-split lightning source can double count it. The
`lightning_coexistence` scenario enables both and checks MIEM accounting only;
it does not interpret total tracer change as an MIEM-only budget.

## Scalability

Each rank constructs MIEM with global `nCells`, the actual MPAS level count,
and only its ordered owned global IDs. UPTEMPO/ECCAD readers sort a temporary
index, coalesce consecutive IDs, issue `nc_get_vara` calls for those runs, and
scatter back into host order. Flux buffers, two cached time brackets, and exact
grid metadata therefore scale with owned cells; MIEM performs no MPI calls.

To measure this on a given system, run the benchmark from the development
repository:

```bash
scripts/benchmark_miem_scalability.sh --case all --warm-steps 12
```

The script is not in the v2026.08.01 release. It expects external init/mesh and
partition files under `$HOME/Data/CheMPAS` by default, creates a temporary
deterministic exact-grid NO/NO2 inventory, and runs full-grid and selected-cell
modes on eight ranks. On the 28,080-cell planar supercell mesh and the
40,962-cell spherical x1.40962 mesh, the selected-cell aggregate NetCDF payload
and persistent state are exactly `1/8` of the replicated full-grid totals,
owned-cell fluxes are identical between the two modes, and no selected rank
holds global-sized flux buffers. The benchmark also records initialization and
warm-step time and peak RSS; those values depend on the system and are not
portable performance thresholds.

## Current limitations

- Inventories must be conservatively remapped onto the exact MPAS grid before
  the run; CheMPAS-A does not regrid at runtime.
- Emissions require the Gregorian calendar.
- Vertical profiles are fixed normalized fractions, not meteorology-dependent
  plume rise.
- Each rank performs independent serial NetCDF hyperslab reads rather than
  collective parallel I/O.
- The full-grid MUSICA constructor remains only for backward compatibility and
  as the benchmark reference; the CheMPAS-A runtime uses selected cells.
- The global chemistry and emissions example uses date-matched meteorology
  but idealized chemical background profiles that are not spun up. It
  demonstrates coupled source attribution; its first-day concentrations are
  not production air-quality predictions.
- All three global example scenarios run with
  `config_physics_suite = 'none'`: there is no boundary-layer mixing,
  convection, or cloud, so TUV-x runs clear-sky and surface emissions are
  carried upward only by resolved motion.

## Related documentation

- [MUSICA integration](MUSICA_INTEGRATION.md)
- [MUSICA API reference](MUSICA_API.md)
- [Architecture](../architecture/ARCHITECTURE.md)
- [Visualization guide](../guides/VISUALIZE.md)
- [Build guide](https://github.com/NCAR/CheMPAS-A/wiki/Building)
- [Getting started](https://github.com/NCAR/CheMPAS-A/wiki/Getting-Started)
- [Global chemistry and emissions](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions)
