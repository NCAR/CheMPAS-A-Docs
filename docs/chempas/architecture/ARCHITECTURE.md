# CheMPAS-A Architecture

This document describes the high-level architecture of CheMPAS-A: the MPAS
(Model for Prediction Across Scales) framework plus the chemistry extensions in
this repository.

## Overview

MPAS is a modular, unstructured mesh framework for Earth system modeling. It supports multiple specialized "cores" for different physical domains:

- **core_atmosphere** - Atmospheric modeling (primary focus of this branch)
- **core_init_atmosphere** - Initialization preprocessing
- **core_ocean** - Ocean modeling
- **core_seaice** - Sea ice modeling
- **core_landice** - Land ice/glacier modeling
- **core_sw** - Shallow water test cases
- **core_test** - Framework testing suite

## Architecture Diagram

```
                        MPAS Main Driver
                         (src/driver/)
                              |
                +-------------+-------------+
                |                           |
          Atmosphere Core             Ocean/Other Core
                |
    +-----------+-----------+
    |           |           |
 Dynamics    Physics    Chemistry
  (SRK3)  (Convection,  (MPAS driver +
           Radiation,   MUSICA/MICM +
           Microphysics, MIEM + TUV-x)
           LSM)               |
                       Runtime tracer
                       discovery from
                       MICM config

   ====================================================
        MPAS Framework (Shared)
        Pools, I/O, DMpar, Logging, Halo, Block Creator
   ====================================================
```

### Chemistry Tracer Flow

Chemistry tracers are **not** defined in `Registry.xml`. They are discovered
at runtime from the MICM configuration file:

```
atm_setup_block
  |-> atm_prepare_runtime_chemistry_vars()    # Queries MICM config
  |     |-> musica_query_species()            #   Creates temp micm_t, reads species
  |-> MPAS_var_add_callback()                 # Registers chemistry runtime-var hook
  |-> atm_generate_pools()                    # Registry + runtime-var generation
  |     |-> Registry tracers (qv, qc, qr...)
  |     |-> Callback appends qXX/tend_qXX
  |     |-> Runtime-var framework adds index_qXX dimensions
  |
  |-> mpas_block_creator allocates arrays     # Uses updated num_scalars for sizing
  |
  ... later ...
  |
chemistry_init
  |-> musica_init()                           # Full MICM solver instance
  |-> resolve_mpas_indices()                  # Finds index_qXX from pool
  |-> chemistry_seed_chem()                   # Seeds MPAS scalars from MICM state
```

Switching chemistry mechanisms requires only changing the MICM config file —
no Fortran source or registry edits.

### Emissions Flow

MIEM is independently selected by `config_miem_file`; an empty value is a
strict no-op. Runtime `emis_<species>` names are nevertheless discovered from
the separate MICM mechanism (`config_micm_file`) because the writable targets
are `EMIS.<species>` MICM rate parameters.

```text
atm_setup_block
  |-> query EMIS.* names from config_micm_file when MIEM is enabled
  |-> parse bounded sector/category/layer diagnostic requests
  |-> append total and explicitly requested emis_* runtime diagnostics
  |
chemistry_init
  |-> collect ordered owned indexToCellID and geometry arrays
  |-> mpas_miem: construct selected-cell state with actual nVertLevels
  |-> cross-match actual MIEM species with MICM species and EMIS.* rates
  |
chemistry_step
  |-> MIEM reads coalesced owned-cell hyperslabs at interval start
  |-> first read validates exact-grid metadata before MICM mutation
  |-> layer flux / (layer depth * molar mass) sets coupled and optional reference state
  |-> successful solve publishes total/group/layer fields and commits mass
  |
chemistry_finalize
  |-> one global reduction and rank-zero per-species mass logs
```

Inventories remain pregridded and prevalidated in exact global MPAS order;
there is no runtime regridding. Each rank retains only its selected owned-cell
flux, bracket, and metadata state. The legacy full-grid MUSICA constructor is
used only by equivalence tests and benchmarks. See
[MIEM_INTEGRATION.md](../musica/MIEM_INTEGRATION.md).

### Phase 9 evidence boundary

```text
tracked external-input manifest
  |-> immutable external inventory, meteorology, mesh, and partition
  |-> isolated G3/A1/R0-R6/E0 runs
  |-> compact reports, logs, field hashes, and figure manifest
  `-> stage9e-release-manifest.json (all hashes, commands, and gates)
```

Large NetCDF inputs, histories, restarts, and baseline outputs stay outside the
repository under `CHEMPAS_EMISSIONS_DATA_ROOT`; only compact, hash-addressed
evidence is tracked. The release proves the implemented data path, coupled
dynamics/transport/chemistry behavior, source and NOy accounting, restart,
controls, and reproducibility. Scientific interpretation is narrower: A1 uses
science-grade emissions and date-matched meteorology, but its idealized,
unspun chemical initial state does not support production first-day
concentration claims.

### Chemistry Timestep Flow

Once initialized, chemistry is stepped through the MPAS chemistry driver after
physics has updated time level 1 and before dynamics advances the transported
state:

```
physics update
  |-> chemistry_step(time level 1)
  |-> dynamics
```

Inside `chemistry_step`, the active chemistry path is:

```
chemistry_step
  |-> config_chemistry_interval gate       # 0.0 = every MPAS step
  |-> solar_cos_sza() or TUV-x input preparation
  |-> tuvx_compute_photolysis() / fallback j = j_max * max(0, cos_sza)
  |-> miem_run() / musica_set_emission_fluxes()
  |-> lightning_nox_inject()                  # Operator-split NO source
  |-> chemistry_from_MPAS()                   # MPAS state -> MICM state
  |-> musica_step()                           # MICM chemistry solve
  |-> chemistry_to_MPAS()                     # MICM state -> MPAS state
```

With positive `config_chemistry_interval`, elapsed dynamics timesteps
accumulate and `chemistry_step` returns before LNOx/MICM work until the
interval is reached. The next chemistry solve uses the accumulated timestep for
both LNOx injection and MICM integration. `config_chem_substeps` only splits a
fired chemistry solve into smaller MICM calls; photolysis j-rates are frozen across `config_chem_substeps`.

Current chemistry-specific modules under `src/core_atmosphere/chemistry/` are:

- `mpas_atm_chemistry.F` - top-level chemistry manager and MPAS coupling
- `mpas_chem_constants.F` - shared chemistry units and physical constants
- `mpas_prescribed_fields.F` - rank-local exact-grid monthly prescribed fields
- `musica/mpas_musica.F` - MUSICA/MICM coupler and state/rate-parameter updates
- `musica/mpas_miem.F` - MIEM lifecycle, owned-cell mapping, and mass accounting
- `mpas_lightning_nox.F` - operator-split lightning NOx source
- `mpas_solar_geometry.F` - fallback solar zenith-angle calculation
- `mpas_tuvx.F` - TUV-x photolysis wrapper, including cloud-radiator support

## Directory Structure

```
CheMPAS-A/
├── CMakeLists.txt          # Retained non-chemistry MPAS CMake path
├── Makefile                # Supported CheMPAS chemistry build
├── cmake/                  # CMake modules and functions
├── docs/                   # Sphinx documentation source
│   ├── chempas/            # CheMPAS-A-specific developer notes
│   ├── tutorial/           # CheMPAS-A tutorial chapters
│   ├── users-guide/        # Imported MPAS-Atmosphere user's guide
│   └── technical-description/
├── micm_configs/           # MICM and TUV-x chemistry configuration files
├── miem_configs/           # MIEM source configuration documents
├── scripts/                # Analysis, plotting, and helper scripts
├── src/                    # Main source code
│   ├── driver/             # Main execution entry points
│   ├── framework/          # Shared infrastructure
│   ├── operators/          # Mathematical operations
│   ├── tools/              # Code generation tools
│   ├── external/           # External libraries (ezxml, SMIOL, ESMF)
│   ├── core_atmosphere/    # Atmosphere modeling
│   ├── core_init_atmosphere/
│   ├── core_ocean/
│   ├── core_seaice/
│   ├── core_landice/
│   ├── core_sw/
│   └── core_test/
└── test_cases/             # Idealized, integration, and global workflows
```

## Core Components

### 1. Framework (`src/framework/`)

The framework provides shared infrastructure used by all cores:

| File | Size | Purpose |
|------|------|---------|
| `mpas_dmpar.F` | 415KB | Distributed memory parallel communication |
| `mpas_io_streams.F` | 180KB | I/O streaming infrastructure |
| `mpas_io.F` | 268KB | Core I/O routines |
| `mpas_pool_routines.F` | 235KB | Data pool management |
| `mpas_stream_manager.F` | 280KB | Stream handling |
| `mpas_field_routines.F` | 118KB | Field manipulation |
| `mpas_block_creator.F` | 94KB | Block decomposition |

Additional services: logging, timekeeping, halo exchanges, forcing, bootstrapping, hash tables.

### 2. Operators (`src/operators/`)

Specialized mathematical kernels:

- `mpas_rbf_interpolation.F` - Radial basis function interpolation
- `mpas_geometry_utils.F` - Geometric calculations
- `mpas_tensor_operations.F` - Tensor computations
- `mpas_vector_operations.F` - Vector routines
- Tracer advection schemes (monotonic, standard)
- Matrix and spline operations

### 3. Driver (`src/driver/`)

Main execution entry points:

- `mpas.F` - Main program
- `mpas_subdriver.F` - Common subdriver for all cores

### 4. External Libraries (`src/external/`)

- `ezxml/` - XML parsing library
- `SMIOL/` - Scalable Modeling I/O Library
- `esmf_time_f90/` - ESMF time management (internal copy)

## Registry System

The `Registry.xml` files define model metadata:

- **Dimensions**: Mesh sizes (nCells, nEdges, nVertices, nVertLevels)
- **Variables**: State variables, diagnostics, tracers
- **Namelists**: Configuration parameters
- **Streams**: I/O definitions (input, output, restart files)

The registry is processed by tools in `src/tools/registry/` to generate Fortran code.

## Data Flow

1. **Initialization**: Driver reads configuration, initializes framework
2. **Domain Decomposition**: Mesh partitioned across MPI ranks
3. **Time Integration**: Core-specific dynamics, physics, and chemistry stepping
4. **Halo Exchange**: Framework handles inter-processor communication
5. **I/O**: Stream manager handles checkpointing and output

## Dependencies

### Supported Chemistry Build

The supported Makefile path for the chemistry-enabled `develop` branch
requires:

- MPI, including the compiler-compatible Fortran interface;
- NetCDF-C and NetCDF-Fortran;
- the PnetCDF C library;
- PIO; and
- the revision-qualified MUSICA-Fortran closure, including MICM, MIEM,
  MechanismConfiguration, and TUV-x.

PnetCDF's Fortran interface is not required by the supported LLVM/flang path;
that reference configuration intentionally builds PnetCDF with its Fortran
bindings disabled. All Fortran module dependencies that are used, including
MPI, NetCDF-Fortran, PIO, and MUSICA-Fortran, must match the selected compiler
ABI.

The retained non-chemistry CMake path has a different dependency scope and
does not expose the CheMPAS chemistry coupling. Optional facilities such as
GPTL or ESMF depend on that selected build configuration. See the build guide
for the authoritative commands and qualified revisions.

## Related Documentation

- [Public MVP build guide](https://github.com/NCAR/CheMPAS-A/wiki/Building) - supported chemistry build and dependency pins
- [COMPONENTS.md](COMPONENTS.md) - Detailed component documentation
- [MUSICA_INTEGRATION.md](../musica/MUSICA_INTEGRATION.md) - Chemistry integration details
- [MIEM_INTEGRATION.md](../musica/MIEM_INTEGRATION.md) - Exact-grid emissions workflow
- [MVP_PRE_RELEASE.md](../mvp/MVP_PRE_RELEASE.md) - Current end-to-end global demonstration
- [TEST_RUNS.md](../results/TEST_RUNS.md) - Recorded runtime validation results
- [MVP qualification record](../mvp/MVP_PRE_RELEASE.md) - completed release-candidate scope and evidence

## External Resources

- MPAS-Atmosphere User Guide: http://mpas-dev.github.io/atmosphere/
- MPAS GitHub: https://github.com/MPAS-Dev
