# MUSICA/MICM Integration in MPAS

This document describes the integration of the MUSICA (Multi-Scale
Infrastructure for Chemistry and Aerosols) chemistry stack into
MPAS-Atmosphere as implemented in CheMPAS-A.

## Overview

The MUSICA integration enables coupled atmospheric-chemistry modeling on
MPAS's unstructured mesh. CheMPAS-A uses MICM (Model Independent Chemistry
Module) as the chemical ODE solver, MIEM (Model Independent Emissions Module)
for pregridded offline surface or normalized-profile emissions, and TUV-x as
the optional photolysis solver. The complete emissions workflow is documented in
[MIEM_INTEGRATION.md](MIEM_INTEGRATION.md).

This integration targets the exact revision closure documented in the
[MUSICA API revision scope](MUSICA_API.md#supported-revision-scope). It is not
compatible with arbitrary same-version installations or the audited 2026-08-16
MUSICA/MIEM `main` tips: the rank-local selected-cell constructor, layer/group
fluxes, exact-grid metadata, and complete static Fortran link closure are on the
CheMPAS feature pins. MICM `main` contains the tested MICM commit but is 29
commits newer and has not been qualified as a drop-in upgrade.

## Architecture

```
  MPAS Atmosphere Core
  ====================

  Dynamics --> Physics --> Chemistry
   (SRK3)    (Radiation,   (mpas_atm_chemistry.F)
             Convection)          |
                                  v
                  +------- mpas_musica.F
                  |        =============
                  |        MICM Solver (Rosenbrock)
                  |        State (Coupled + Reference)
                  |
                  +------- mpas_tuvx.F / mpas_solar_geometry.F
                  |        Photolysis rates
                  |        + mpas_prescribed_fields.F monthly upper O3
                  |
                  +------- mpas_miem.F
                  |        Selected-cell offline emissions
                  |        exact-grid validation + layer/group flux
                  |
                  +------- mpas_lightning_nox.F
                           Operator-split NO source
```

## Source Files

| File | Location | Purpose |
|------|----------|---------|
| `mpas_atm_chemistry.F` | `src/core_atmosphere/chemistry/` | Top-level chemistry init/step/finalize driver, MPAS gather/scatter, photolysis update gating |
| `mpas_musica.F` | `src/core_atmosphere/chemistry/musica/` | MUSICA/MICM state management, species mapping, unit conversion, photolysis-rate writes |
| `mpas_miem.F` | `src/core_atmosphere/chemistry/musica/` | Selected-cell MIEM lifecycle, exact-grid validation, column/layer/group fluxes, and emitted-mass accounting |
| `mpas_tuvx.F` | `src/core_atmosphere/chemistry/` | TUV-x setup, host-column profile updates, optional upper-atmosphere extension, cloud optical depth |
| `mpas_prescribed_fields.F` | `src/core_atmosphere/chemistry/` | Exact-grid selected-cell monthly O3 provider for the TUV-x column strictly above the model top |
| `mpas_solar_geometry.F` | `src/core_atmosphere/chemistry/` | Fallback solar zenith-angle calculation |
| `mpas_lightning_nox.F` | `src/core_atmosphere/chemistry/` | Operator-split lightning NO source |

## Conditional Compilation

The integration is conditionally compiled using the `MPAS_USE_MUSICA` preprocessor flag:

```fortran
#ifdef MPAS_USE_MUSICA
    use mpas_musica, only: musica_init
    ...
#endif
```

Enable at build time with the Makefile workflow used by this repository:

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

`scripts/check_build_env.sh --export` resolves and exports the supported
compiler target as `CHEMPAS_MAKE_TARGET` together with the dependency paths.

## API Overview

### Chemistry Interface (`mpas_atm_chemistry`)

| Routine | Purpose |
|---------|---------|
| `chemistry_init()` | Initialize chemistry packages |
| `chemistry_step()` | Advance chemistry one timestep |
| `chemistry_finalize()` | Clean up resources |
| `chemistry_from_MPAS()` | Extract MPAS state for chemistry |
| `chemistry_to_MPAS()` | Update MPAS state from chemistry |
| `chemistry_seed_chem()` | Seed MPAS chemistry tracers from MICM initial state |
| `chemistry_query_species()` | Query MICM config for runtime chemistry species |
| `chemistry_query_emission_species()` | Query `config_micm_file` for runtime `EMIS.*` diagnostics |
| `chemistry_prepare_tracer_outputs()` | Validate MMR/VMR output selections and cache conversion descriptors |
| `chemistry_add_tracer_output_vars()` | Register output-only `vmr_<species>` diagnostics |
| `chemistry_compute_tracer_outputs()` | Fill requested VMR diagnostics immediately before history output |

### MUSICA Interface (`mpas_musica`)

| Routine | Purpose |
|---------|---------|
| `musica_init()` | Initialize MICM solver and state |
| `musica_query_species()` | Lightweight species discovery for runtime tracer allocation |
| `musica_step()` | Solve chemistry (coupled state) |
| `musica_step_ref()` | Solve chemistry (reference state) |
| `musica_finalize()` | Clean up MICM resources |
| `MICM_from_chemistry()` | Copy MPAS tracers to MICM |
| `MICM_to_chemistry()` | Copy MICM results to MPAS |
| `resolve_mpas_indices()` | Resolve `index_q*` dimensions for all chemistry species |
| `micm_to_mpas_chem()` | Seed MPAS with MICM initial state (generic species loop) |
| `log_column_comparison()` | Diagnostic logging |
| `copy_state_to_ref()` | Sync reference state |
| `musica_cache_photo_indices()` | Cache MICM `PHOTO.<name>` rate-parameter indices |
| `musica_set_photolysis_rates()` | Write the current photolysis-rate field into MICM state |
| `musica_query_emission_species()` | Discover `EMIS.*` rate parameters from the MICM mechanism |
| `musica_cache_emission_indices()` | Cross-match MIEM species with writable MICM species/rates |
| `musica_set_emission_fluxes()` | Convert every MIEM layer mass flux to matching MICM molar rates |

### Emissions Interface (`mpas_miem`)

| Routine | Purpose |
|---------|---------|
| `miem_init()` | Construct MIEM with global dimensions, actual levels, ordered owned IDs, and bounded diagnostic selection |
| `miem_get_species()` | Return actual MIEM output species for MICM cross-matching |
| `miem_run()` | Interpolate selected hyperslabs, validate first-read grid metadata, and return owned column/layer fluxes |
| `miem_get_diagnostic_selection()` | Return sanitized bounded sector/category/layer selections |
| `miem_get_diagnostic_fluxes()` | Return requested owned-cell group column/layer buffers |
| `miem_commit_mass()` | Accumulate successful-step rank-local emitted or signed net-exchange mass |
| `miem_finalize()` | Reduce/log final species totals and release MIEM |

## Data Flow

MPAS calls the chemistry driver after physics has updated time level 1 and
before the dynamics advance. Chemistry therefore operates on time level 1
tracer, thermodynamic, and diagnostic fields, then dynamics transports the
updated tracer state.

`config_chemistry_interval` can reduce the chemistry call frequency. The
default `0.0` runs chemistry every MPAS step. Positive values accumulate elapsed
dynamics timesteps and return before the MIEM/LNOx/MICM work until the interval
is reached; when chemistry fires, MIEM sampling, LNOx injection, and the MICM
solve use the accumulated chemistry timestep.

### Each Chemistry Timestep

1. **Photolysis update** (`tuvx_compute_photolysis` or fallback `cos(SZA)`)
   - Compute rate parameters such as `PHOTO.jNO2`
   - Write them to MICM through `musica_set_photolysis_rates`
   - Mirror available rates to diagnostics such as `j_jNO2`

2. **Offline emissions** (`miem_run`, `musica_set_emission_fluxes`)
   - Sample only owned global IDs at the chemistry interval start
   - On first read, compare selected IDs, area, and required coordinates with MPAS
   - Require finite layer fluxes whose sum closes to each column; negative
     values are allowed only for exact species opted into signed surface exchange
   - Set every populated `EMIS.<species>` layer in the coupled state and, when
     enabled, the reference state

3. **Lightning NOx source** (`lightning_nox_inject`)
   - Adds operator-split NO to `qNO` when the active mechanism contains NO

4. **MPAS -> MICM** (`chemistry_from_MPAS`)
   - Extract scalars (tracers), temperature, pressure, density from MPAS pools
   - Convert mixing ratios [kg/kg] to concentrations [mol/m³]
   - Set MICM environmental conditions

5. **MICM Solve** (`musica_step`)
   - Rosenbrock ODE integration
   - Solve coupled state (advected by MPAS)
   - Optionally solve reference state (chemistry only, for diagnostics)
   - Optionally split the chemistry timestep into `config_chem_substeps` calls
   - Photolysis j-rates are frozen across `config_chem_substeps`

6. **MICM -> MPAS** (`chemistry_to_MPAS`)
   - Convert concentrations [mol/m³] to mixing ratios [kg/kg]
   - Update MPAS scalar tracers

### Unit Conversion

```
MPAS → MICM:  C = q × ρ_dry / M_species
MICM → MPAS:  q = C × M_species / ρ_dry

where:
  C = concentration [mol/m³]
  q = dry-air mass mixing ratio [kg/kg dry air]
  ρ_dry = dry-air mass density [kg dry air/m³]
  M_species = molar mass [kg/mol]
```

This `ρ_dry` is distinct from MICM's environmental
`state%conditions%air_density`, which is the total moist molar density
`p / (R T)` in mol m⁻³. CheMPAS-A uses `rho_dry = zz * rho_zz` for the tracer
conversions and derives the MICM condition from pressure and temperature.

The transported and restarted `q<species>` fields always remain dry-air mass
mixing ratios. `config_chem_tracer_output_unit` and exact per-species
`config_chem_tracer_output_overrides` can add history-only
`vmr_<species>` companions in `fraction`, `percent`, `ppmv`, `ppbv`, or `pptv`:

```text
vmr_output = q * M_air / M_species * unit_scale
```

The default `mmr` selection adds no companion fields. These diagnostics never
feed back into MICM or transport and are not automatically written to restart
streams.

## Mechanism Configuration

The coupling is mechanism-agnostic. Chemistry species are read from the MICM
configuration at runtime, and MPAS tracer names follow the convention:

`MICM species X -> MPAS tracer qX`

The shipped mechanisms include ABBA (`AB`, `A`, `B`), LNOx-O3 (`NO`, `NO2`,
`O3`), Chapman, Chapman + NOx, and reduced Ox-HOx-NOx-CO-CH4 variants. The
`global_cams_*` snapshots add exactly `EMIS.NO` and `EMIS.NO2` for the
[global tropospheric NOx ladder](GLOBAL_TROPOSPHERIC_NOX.md). MICM species map
to MPAS tracers by prefixing `q`, e.g. `NO2 -> qNO2` and `O3 -> qO3`.

The [global methane workflow](GLOBAL_TROPOSPHERIC_METHANE.md) adds a Tier C
`EMIS.CH4` entry point and a deterministically generated MOZART-35 tier. Its
O2, N2, and H2O parameters are host-bound only when the mechanism metadata
declares that relationship; transported `qO2` in Chapman and Tier C remains
unchanged.

Molar masses are read per-species from MICM properties (`__molar mass`) via
`micm%get_species_property_double(...)` during `musica_init`.

## Grid Cell Mapping

MICM processes a 1D array of grid cells. The mapping between MPAS's 2D (cell, level) indexing and MICM's 1D indexing:

```fortran
! MPAS: scalars(tracer, level, cell)
! MICM: state%concentrations(flat_index)

! MICM cell index = (iCell - 1) * nVertLevels + k
micm_cell = (iCell - 1) * nVertLevels + k

! MICM array index (strided)
idx = 1 + (micm_cell - 1) * cell_stride + (species - 1) * var_stride
```

## Optional Reference State Tracking

The integration always maintains the coupled state and allocates the reference
state only when `config_chemistry_ref_solve = .true.`:

1. **Coupled State** (`state`)
   - Updated each timestep from MPAS
   - Experiences advection through MPAS tracer transport
   - Results written back to MPAS

2. **Reference State** (`state_ref`)
   - Seeded once from the coupled state on the first chemistry step
   - Receives the same photolysis and MIEM rate parameters
   - Does not receive subsequent MPAS advection, environmental recoupling, or
     operator-split LNOx injections

Their difference is therefore a chemistry-only reference comparison, not an
unconditional pure-advection attribution: it includes transport as well as the
effects of omitted environmental recoupling and later LNOx injections. It
isolates transport only when those other inputs remain static or absent.

## Runtime Tracer Resolution

Chemistry tracers are not statically defined in `Registry.xml`. During
`atm_setup_block`, MPAS queries MICM species and extends `scalars` and
`scalars_tend` metadata dynamically.

During `chemistry_init`, `resolve_mpas_indices()` then resolves each
`index_q*` dimension from the state pool. Missing/invalid indices are treated
as initialization errors.

Runtime chemistry tracers are currently guarded against `config_apply_lbcs=true`
because `lbc_scalars` remains statically sized from registry metadata.

## Configuration

### Namelist Options

```fortran
&chemistry
    config_micm_file = 'miem_nox.yaml'
    config_chem_tracer_output_unit = 'mmr'
    config_chem_tracer_output_overrides = 'O3=ppmv,NO=ppbv,NO2=ppbv'
/

&emissions
    config_miem_file = 'chem_box_nox.yaml'
    config_miem_net_flux_species = ''
    config_miem_diagnostic_sectors = ''
    config_miem_diagnostic_categories = ''
    config_miem_layered_diagnostics = .false.
    config_miem_max_diagnostic_fields = 256
/

&photolysis
    config_tuvx_config_file = 'tuvx_no2.json'
    config_tuvx_top_extension = .false.
    config_tuvx_upper_column_mode = 'none'
/
```

### MICM Configuration File

The MICM solver reads its mechanism from the YAML file named by
`config_micm_file`. The repository's current mechanism files live in
`micm_configs/` and specify:
- Chemical species
- Reactions
- Rate constants
- Initial concentrations

The MIEM mechanism-configuration document is separate. An empty
`config_miem_file` disables MIEM without disabling MICM chemistry. Both paths,
and inventory paths inside the MIEM YAML, are resolved from the run directory.
One MIEM YAML may declare multiple inventory files; each is sampled
independently, must carry the same validated exact-grid mesh identity, and is
combined through the configured source/category/hierarchy rules. MIEM
inventories must be pregridded and validated; CheMPAS-A performs no runtime
regridding. MIEM sources may use `vertical injection: surface` or a fixed
normalized `vertical profile` with exactly one fraction per MPAS level.
`config_miem_net_flux_species` is an exact-name exception that permits positive
upward and negative downward surface exchange; every other species remains
finite and nonnegative. The optional namelist requests publish only named
sectors/categories and are rejected before allocation when
`species * requested_groups * levels` exceeds the configured cap.

## Diagnostic Output

The integration logs diagnostic information:

```
[MUSICA] Initializing MICM chemistry package...
MICM version: X.Y.Z
MICM number of grid cells: 163840

[MUSICA] MICM species: AB
[MUSICA] MICM species: A
[MUSICA] MICM species: B

[MIEM] Initialized selected-cell emissions object: 8 of 64 cells, 60 levels, 2 species.
[MIEM] Validated selected exact-grid inventory metadata: ...
[MIEM] Emissions species: NO
[MIEM] Emissions species: NO2

[MUSICA] Stepping MICM solver...
[MUSICA] MICM Solver statistics ...
  MICM function calls: 5
  MICM jacobian updates: 2
  MICM number of steps: 1
  ...

[COMPARE] Probe cell=512: Coupled vs Reference (chemistry-only)
[COMPARE] Level | AB_coupled AB_ref | A_coupled A_ref | B_coupled B_ref

[MIEM] Total emitted mass for NO: ... kg
[MIEM] Total emitted mass for NO2: ... kg
[MIEM] Net applied surface exchange mass for CH4: ... kg
```

The first label is used for source-only species. The second is used only for a
species explicitly selected by `config_miem_net_flux_species`; its accumulated
value is algebraic and can be negative.

Enabled runs write `emis_<species>` column-flux diagnostics in
`kg m^{-2} s^{-1}`. Explicit requests add `emis_<species>_layer`,
`emis_<species>__sector_<label>`, and
`emis_<species>__category_<id>` families (plus `_layer` forms). They are zero
initially and then represent the last successful chemistry interval's
interval-start flux. No disaggregated buffers are allocated by default.

## Dependencies

The module names below refer to the revision-qualified package, especially the
expanded feature-pin `musica_emissions` module. Audited MUSICA `main` has a
module with the same name but only the smaller full-grid surface-flux API.

| Dependency | Module | Purpose |
|------------|--------|---------|
| `musica_micm` | `micm_t` | MICM solver type |
| `musica_micm` | `solver_stats_t` | Solver statistics |
| `musica_micm` | `RosenbrockStandardOrder` | Solver type constant |
| `musica_state` | `state_t` | Chemical state type |
| `musica_emissions` | `mechanism_t`, `emissions_t`, `emissions_grid_metadata_t` | MIEM configuration, selected column/layer/group state, and exact-grid metadata |
| `musica_util` | `error_t` | Error handling |
| `musica_util` | `string_t` | String utilities |

## Error Handling

Errors from MUSICA are captured and propagated:

```fortran
type(error_t) :: error

call micm%solve(time_step, state, solver_state, solver_stats, error)
if (has_error_occurred(error, error_message, error_code)) return
```

The `has_error_occurred()` helper converts MUSICA errors to MPAS-compatible format.

## Current Status And Follow-On Work

The 2026-08-16 `develop` audit distinguishes implemented/qualified software
from experiments whose science promotion is still incomplete:

| Capability | Status |
|---|---|
| Core coupling | Implemented: runtime species/tracer discovery, MPAS-MICM MMR/concentration transfer, configurable substeps/tolerance, optional reference solve, and LNOx-O3, Chapman, Chapman-NOx, Tier C, and generated Tier Z mechanism paths. |
| TUV-x and prescribed O3 | Implemented: from-host atmosphere/cloud profiles, optional exact-grid cyclic monthly MERRA-2 O3 strictly above the model top, and legacy/no-extension modes. Prescribed upper O3 affects photolysis only and never writes prognostic `qO3`. |
| MIEM and multiple inventories | Implemented: selected owned-cell reads, exact-grid validation, surface/fixed-profile allocation, multiple inventory files in one configuration, bounded total/layer/sector/category diagnostics, signed-species opt-in, and algebraic global mass budgets. The global MVP exercised separate CAMS anthropogenic and FINN fire inventories. |
| Global MVP | Complete as a pre-release process demonstration. The x1.40962 No Surface Emissions, Anthropogenic Emissions, and Anthropogenic + Fire Emissions 24-hour attribution with reduced chemistry and the complete regression suite passed; the result is not a production air-quality forecast or chemically spun-up product. |
| Chemistry output units | Complete and revalidated: MMR remains authoritative transport/restart state; optional history-only `vmr_<species>` diagnostics support fraction, percent, ppmv, ppbv, and pptv with per-species overrides and host-bound species. |
| MOZART-35 / global methane | The deterministic 35-transported-tracer mechanism, host-bound O2/N2/H2O handling, user rates, ledgers, MIEM NOx+CH4 path, and independent 48-hour box qualification are implemented. The global methane science ladder is not complete because CAMS inversion access and the documented disk-capacity gate remain unresolved. |
| Scalability | Regional/global reports demonstrate owned-cell payload/state scaling and bitwise full/selected equivalence on eight ranks. I/O remains independent serial NetCDF hyperslabs rather than collective parallel I/O. |

Follow-on work includes science promotion and longer validation for MOZART-35,
additional production-oriented chemistry evaluation, aerosol chemistry,
performance work for expensive photolysis configurations, collective
parallel-NetCDF MIEM I/O, and meteorology-dependent plume rise beyond fixed
normalized profiles.

## Related Documentation

- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - Overall system architecture
- [Public MVP build guide](https://github.com/NCAR/CheMPAS-A/wiki/Building) - Build configuration for MUSICA
- [COMPONENTS.md](../architecture/COMPONENTS.md) - Atmosphere component details
- [MIEM_INTEGRATION.md](MIEM_INTEGRATION.md) - Offline-emissions workflow and contracts
- [GLOBAL_TROPOSPHERIC_METHANE.md](GLOBAL_TROPOSPHERIC_METHANE.md) - Methane backgrounds, surface exchange, and MOZART-35
- [MVP_PRE_RELEASE.md](../mvp/MVP_PRE_RELEASE.md) - Completed global MVP scope and limits
- [CHEM_TRACER_OUTPUT_UNITS_PLAN.md](../CHEM_TRACER_OUTPUT_UNITS_PLAN.md) - VMR diagnostic implementation and verification
