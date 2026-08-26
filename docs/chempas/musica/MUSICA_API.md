# MUSICA API Reference

This document is a compatibility reference for the MUSICA (Multi-Scale
Infrastructure for Chemistry and Aerosols) Fortran API used by CheMPAS-A. The
active build discovers an installed MUSICA-Fortran package through
`pkg-config`; sibling source checkouts such as `../MUSICA`, `../MICM`, and
`../MIEM` are useful for inspection but are not hard-coded build inputs.

## Table of Contents

1. [Supported Revision Scope](#supported-revision-scope)
2. [Module Overview](#module-overview)
3. [MICM Solver API](#micm-solver-api)
4. [State Management API](#state-management-api)
5. [Utility Types](#utility-types)
6. [Error Handling](#error-handling)
7. [Configuration Files](#configuration-files)
8. [Solver Types](#solver-types)
9. [Usage Patterns](#usage-patterns)
10. [Unit Conversions](#unit-conversions)
11. [Related Documentation](#related-documentation)

---

## Supported Revision Scope

Unless a paragraph explicitly says `main`, every Fortran type, signature, and
behavior below is scoped to the exact dependency closure qualified by
CheMPAS-A `develop`:

| Component | Supported revision |
|---|---|
| MUSICA-Fortran | `1403e3d22717bc87f3bf9d0aa591caf039c92bbc` (`0.16.5`) |
| MICM | `bb57684a2047f0e58f30b199366294af879e8597` |
| MIEM | `9fdf14a189262eecb677862d877ab72b06c95e21` |
| MechanismConfiguration | `82c159ae6d74934318ffd6c405a45c2159065b12` |
| TUV-x | `bbf7dd9a144fa0f0294b3779f3f993818638e20c` |

The selected-cell emissions constructor, per-layer and grouped fluxes,
exact-grid metadata, and the complete static `pkg-config` closure are feature
pin capabilities. A version string of `0.16.5` alone does not establish that
an installation has them; the build preflight checks the exported source and
dependency revisions as well as the Fortran compiler ABI.

### Audited upstream `main` tips

The sibling local `main` and `origin/main` refs were equal when audited on
2026-08-16. They are valuable upstream references, but they are not a tested
replacement for the closure above.

| Component | Current role | Audited `main` tip | Compatibility with the CheMPAS-A pin |
|---|---|---|---|
| MUSICA | Build/package umbrella and language bindings for MICM, MIEM, TUV-x, and other components | `a6d34d38f874574b8a0599540f1a12230063ce58` | **Not API-compatible for CheMPAS emissions.** The pin and `main` diverge after `5e4108cceae1aa11478902c996e473d85b41f6ba`; the selected-cell/layer/group/grid-metadata Fortran work is not on `main`. |
| MICM | C++20 chemical state, reaction, and ODE-solver library; the CPU target is header-only and CUDA is optional | `97ac9e5d8aadd345c242722ee8274d71dfe0f73e` (`3.13.0`) | The CheMPAS pin is an ancestor and `main` is 29 commits ahead, but that newer API and numerics have not been qualified with CheMPAS-A. Do not silently substitute it. |
| MIEM | Compiled C++20 offline-emissions library linked with NetCDF; MUSICA supplies its C and Fortran bindings | `970e9c20360e25c53b37d5587eebfc81a18336e2` (`0.1.0`) | **Not API-compatible for CheMPAS emissions.** The pin and `main` diverge after `2bb1e21dc251e3eb356fd0a2d4ae74f7fc145150`; the selected-cell, vertical-profile, diagnostics, and exact-grid work is feature-only. |

In particular, audited MUSICA `main` exports a much smaller
`musica_emissions` Fortran API: `mechanism_t`, a full-grid
`emissions_t(mechanism,n_cells,n_vert_levels,error)` constructor, `run()`,
`flux()`, the surface-flux pointer and strides, and species ordering. It does
not expose global-versus-local dimensions, selected IDs, layer fluxes,
sector/category buffers, or `emissions_grid_metadata_t`. MIEM itself is a C++
library and does not provide a separate Fortran module; these two different
Fortran surfaces are MUSICA bindings at different revisions.

### Authoritative upstream examples

The following paths are relative to the CheMPAS-A repository root and were
checked on the audited upstream `main` tips. They are useful demonstrations of
the component roles, but their main-tip API does not override the supported
pin contract above.

| Purpose | Authoritative path |
|---|---|
| Minimal MUSICA Fortran MIEM box | `../MUSICA/fortran/examples/miem_nox_box_model.F90` |
| Real-fixture Fortran flux-to-`EMIS.*` conversion and solve loop | `../MUSICA/fortran/examples/miem_nox_box_model_real_fixture.F90` |
| Multi-inventory CAMS+FINN Python box | `../MUSICA/python/musica/examples/miem_cams_finn_box_model_real_fixture.py` |
| Matching CAMS+FINN emissions configuration | `../MUSICA/configs/miem/cams_finn_all_species_emissions_config.yaml` |
| Canonical MICM C++ builder/state/solve tutorial | `../MICM/test/tutorial/test_README_example.cpp` |
| Canonical MIEM C++ builder/run tutorial | `../MIEM/test/tutorial/test_README_example.cpp` |
| MIEM real-fixture provenance and field descriptions | `../MIEM/test/data/README.md` |

For the exact extended Fortran declaration used here, inspect the pinned source
without switching the sibling worktree:

```bash
git -C ../MUSICA show \
  1403e3d22717bc87f3bf9d0aa591caf039c92bbc:fortran/miem/emissions.F90
```

---

## Module Overview

### Required Modules

```fortran
use musica_micm   ! MICM solver interface
use musica_emissions ! Pinned extended MIEM mechanism/emissions interface
use musica_state  ! State management
use musica_util   ! Utility types (error_t, string_t, mappings_t)
```

### Key Types

| Type | Module | Purpose |
|------|--------|---------|
| `micm_t` | `musica_micm` | MICM solver instance |
| `mechanism_t` | `musica_emissions` | Parsed MIEM mechanism configuration |
| `emissions_t` | `musica_emissions` | MIEM global/local dimensions, selected IDs, column/layer/group fluxes, and exact-grid metadata |
| `emissions_grid_metadata_t` | `musica_emissions` | Immutable selected inventory identity and geometry after `run()` |
| `state_t` | `musica_state` | Chemical state container |
| `conditions_t` | `musica_state` | Environmental conditions (T, P, rho) |
| `solver_stats_t` | `musica_micm` | Solver performance statistics |
| `error_t` | `musica_util` | Error handling |
| `string_t` | `musica_util` | String wrapper |
| `mappings_t` | `musica_util` | Name-to-index mappings |

The expanded emissions types in this table are available at the supported
MUSICA feature pin. They must not be inferred from MUSICA `main` solely because
that branch also provides a module named `musica_emissions`.

`strides_t` is a private implementation type in `musica_state`; applications
cannot import it with a `use ... only` statement. Its values remain accessible
through the public `state_t%species_strides` and
`state_t%rate_parameters_strides` components described below.

---

## MICM Solver API

### `micm_t` Type

```fortran
type :: micm_t
contains
  procedure :: solve
  procedure :: get_state
  procedure :: get_maximum_number_of_grid_cells
  procedure :: get_species_property_string
  procedure :: get_species_property_double
  procedure :: get_species_property_int
  procedure :: get_species_property_bool
end type micm_t
```

### Constructor

```fortran
type(micm_t), pointer :: micm
type(error_t) :: error

micm => micm_t(config_path, solver_type, error)
```

**Parameters:**
- `config_path` (character) - Path to configuration file or directory
- `solver_type` (integer) - Solver type constant (see [Solver Types](#solver-types))
- `error` (error_t, inout) - Error status

### solve()

Integrates the chemical system forward in time.

```fortran
call micm%solve(time_step, state, solver_state, solver_stats, error)
```

**Parameters:**
- `time_step` (real64, in) - Time step in seconds
- `state` (state_t, inout) - Chemical state
- `solver_state` (string_t, out) - Solver status ("Converged" or error)
- `solver_stats` (solver_stats_t, out) - Performance statistics
- `error` (error_t, inout) - Error status

### get_state()

Creates a new chemical state for the specified number of grid cells.

```fortran
type(state_t), pointer :: state
state => micm%get_state(number_of_grid_cells, error)
```

**Parameters:**
- `number_of_grid_cells` (integer, in) - Number of grid cells
- `error` (error_t, inout) - Error status

**Returns:** Pointer to new `state_t` instance

### get_species_property_*()

Query species properties from configuration.

```fortran
! String property
character(len=:), allocatable :: name
name = micm%get_species_property_string(species_name, property_name, error)

! Double property
real(real64) :: value
value = micm%get_species_property_double(species_name, property_name, error)

! Integer property
integer :: ivalue
ivalue = micm%get_species_property_int(species_name, property_name, error)

! Boolean property
logical :: flag
flag = micm%get_species_property_bool(species_name, property_name, error)
```

**Common Property Names:**
- `"__molar mass"` - Molar mass (used by CheMPAS-A runtime coupling)
- `"molecular weight [kg mol-1]"` - Legacy/alternate molar-mass key in some MICM examples
- `"__long name"` - Full species name
- `"__atoms"` - Number of atoms
- `"__do advect"` - Advection flag
- `"__initial concentration"` - Initial concentration
- `"__absolute tolerance"` - Solver tolerance

### get_maximum_number_of_grid_cells()

```fortran
integer :: max_cells
max_cells = micm%get_maximum_number_of_grid_cells()
```

**Returns:** Maximum grid cells supported by solver type
- Vector-ordered solvers: the build-time vector group size (4 in the qualified
  MICM build)
- Standard-ordered solvers: effectively unlimited; the Fortran wrapper caps
  the C++ `size_t` result at the largest default Fortran integer

### Version Information

```fortran
use musica_micm, only: get_micm_version
type(string_t) :: version
version = get_micm_version()
print *, version%value_
```

### CUDA Availability

```fortran
use musica_micm, only: is_cuda_available
logical :: cuda_ok
cuda_ok = is_cuda_available(error)
```

---

## State Management API

### `state_t` Type

```fortran
type :: state_t
  type(conditions_t), pointer :: conditions(:)     ! Environmental conditions
  real(real64), pointer :: concentrations(:)       ! Species concentrations
  real(real64), pointer :: rate_parameters(:)      ! User-defined rate constants
  type(mappings_t), pointer :: species_ordering    ! Species name→index
  type(mappings_t), pointer :: rate_parameters_ordering
  integer :: number_of_grid_cells
  integer :: number_of_species
  integer :: number_of_rate_parameters
  type(strides_t) :: species_strides
  type(strides_t) :: rate_parameters_strides
contains
  procedure :: update_references
end type state_t
```

### `conditions_t` Type

Environmental conditions for each grid cell.

```fortran
type, bind(c) :: conditions_t
  real(c_double) :: temperature   ! [K]
  real(c_double) :: pressure      ! [Pa]
  real(c_double) :: air_density   ! [mol/m³]
end type conditions_t
```

### State Stride Components

`strides_t` is private to `musica_state`, but its two values are exposed through
public `state_t` components and may be read directly:

```fortran
cell_stride = state%species_strides%grid_cell
variable_stride = state%species_strides%variable
```

### Accessing Concentrations

Concentrations use strided array access:

```fortran
integer :: cell_stride, var_stride, idx, species_idx, cell_idx
real(real64) :: concentration

cell_stride = state%species_strides%grid_cell
var_stride = state%species_strides%variable

! Get species index by name
species_idx = state%species_ordering%index("O3", error)

! Compute array index for cell_idx, species_idx
idx = 1 + (cell_idx - 1) * cell_stride + (species_idx - 1) * var_stride

! Read or write concentration
concentration = state%concentrations(idx)
state%concentrations(idx) = new_value
```

### Accessing Rate Parameters

Same strided pattern as concentrations:

```fortran
integer :: param_idx, idx
real(real64) :: rate

param_idx = state%rate_parameters_ordering%index("PHOTO.jO3", error)

cell_stride = state%rate_parameters_strides%grid_cell
var_stride = state%rate_parameters_strides%variable

idx = 1 + (cell_idx - 1) * cell_stride + (param_idx - 1) * var_stride
state%rate_parameters(idx) = rate_value
```

### Setting Environmental Conditions

```fortran
do i = 1, state%number_of_grid_cells
  state%conditions(i)%temperature = T(i)      ! [K]
  state%conditions(i)%pressure = P(i)         ! [Pa]
  state%conditions(i)%air_density = rho(i)    ! [mol/m³]
end do
```

### update_references()

The public method refreshes the Fortran concentration pointer after the C++
state swaps its backing storage. Normal callers must **not** add a separate
call after `micm%solve()`: at the supported MUSICA pin, `micm_t%solve()` calls
`state%update_references(error)` internally before it returns.

Use the method directly only when code bypasses the normal Fortran solve path
and performs a lower-level operation that can change the C-owned concentration
pointer:

```fortran
call state%update_references(error)
```

### Cleanup

```fortran
deallocate(state)  ! Calls finalizer automatically
deallocate(micm)
```

---

## Utility Types

### `mappings_t` - Name/Index Mappings

```fortran
type :: mappings_t
contains
  procedure :: name   ! Get name by position
  procedure :: index  ! Get index by name or position
  procedure :: size   ! Number of entries
end type mappings_t
```

**Usage:**

```fortran
integer :: n, i, idx
character(len=:), allocatable :: species_name

! Number of species
n = state%species_ordering%size()

! Iterate over all species
do i = 1, n
  species_name = state%species_ordering%name(i)
  idx = state%species_ordering%index(i)
  print *, "Species ", i, ": ", species_name, " at index ", idx
end do

! Lookup by name
idx = state%species_ordering%index("O3", error)
```

### `string_t` - String Wrapper

```fortran
type :: string_t
  character(len=:), allocatable :: value_
contains
  procedure :: get_char_array
end type string_t
```

**Usage:**

```fortran
type(string_t) :: solver_state
character(len=:), allocatable :: status

! After solve
if (solver_state%get_char_array() == "Converged") then
  ! Success
end if

! Or access directly
status = solver_state%value_
```

### `solver_stats_t` - Solver Statistics

```fortran
type :: solver_stats_t
contains
  procedure :: function_calls     ! Number of RHS evaluations
  procedure :: jacobian_updates   ! Jacobian recalculations
  procedure :: number_of_steps    ! Integration steps taken
  procedure :: accepted           ! Accepted steps
  procedure :: rejected           ! Rejected steps
  procedure :: decompositions     ! LU decompositions
  procedure :: solves             ! Linear system solves
  procedure :: final_time         ! Actual integration time [s]
end type solver_stats_t
```

**Usage:**

```fortran
call micm%solve(dt, state, solver_state, stats, error)

print *, "Function calls: ", stats%function_calls()
print *, "Steps: ", stats%number_of_steps()
print *, "Accepted/Rejected: ", stats%accepted(), "/", stats%rejected()
print *, "Final time: ", stats%final_time()
```

---

## Error Handling

### `error_t` Type

```fortran
type :: error_t
contains
  procedure :: code        ! Error code (integer)
  procedure :: category    ! Error category (string)
  procedure :: message     ! Error message (string)
  procedure :: is_success  ! True if no error
  procedure :: is_error    ! Check for specific error
end type error_t
```

### Error Codes

Code 0 denotes success for every category. Nonzero codes are meaningful only
together with the exact category returned by `error%category()`.

**`MUSICA Error`:**

| Code | Meaning |
|------|---------|
| 1 | Unknown error |
| 2 | Mapping not found |
| 3 | Mapping options undefined |

**`MUSICA MICM Error`:**

| Code | Meaning |
|------|---------|
| 1 | Species not found |
| 2 | Solver type not found |
| 3 | Unsupported solver/state pair |
| 4 | Null pointer |

**`MUSICA Parse Error`:**

| Code | Meaning |
|------|---------|
| 1 | Parsing failed |
| 2 | Invalid config file |
| 3 | Unsupported version |
| 4 | Failed to cast to version |

**`MUSICA MIEM Error`:**

| Code | Meaning |
|------|---------|
| 2 | Unresolved reference |
| 3 | Null pointer |

### Usage Pattern

```fortran
type(error_t) :: error

call micm%solve(dt, state, solver_state, stats, error)

if (.not. error%is_success()) then
  print *, "Error category: ", error%category()
  print *, "Error code: ", error%code()
  print *, "Message: ", error%message()
  return
end if
```

### Recommended Helper Function

```fortran
logical function has_error_occurred(error, error_message, error_code)
  use musica_util, only: error_t
  type(error_t), intent(in) :: error
  character(len=:), allocatable, intent(out) :: error_message
  integer, intent(out) :: error_code
  character(len=30) :: code_str

  if (error%is_success()) then
    error_code = 0
    error_message = ''
    has_error_occurred = .false.
  else
    error_code = error%code()
    write(code_str, '(I30)') error_code
    error_message = '[MUSICA Error]: ' // error%category() // &
                    '[' // trim(adjustl(code_str)) // ']: ' // error%message()
    has_error_occurred = .true.
  end if
end function
```

---

## Configuration Files

### v0 Format (Legacy - Directory)

Directory containing multiple JSON files:

```
config_directory/
├── config.json      # Points to other files
├── species.json     # Species definitions
└── reactions.json   # Reaction mechanisms
```

**config.json:**
```json
{
  "camp-files": ["species.json", "reactions.json"]
}
```

**species.json:**
```json
{
  "camp-data": [
    {
      "name": "O3",
      "type": "CHEM_SPEC",
      "molecular weight [kg mol-1]": 0.048,
      "__long name": "ozone",
      "__do advect": true,
      "__initial concentration": 8.1e-6
    }
  ]
}
```

**reactions.json:**
```json
{
  "camp-data": [
    {
      "type": "ARRHENIUS",
      "A": 2.9e19,
      "reactants": {"O": {"qty": 1}, "O2": {"qty": 1}},
      "products": {"O3": {"qty": 1}}
    },
    {
      "type": "PHOTOLYSIS",
      "name": "jO2",
      "reactants": [{"species name": "O2"}],
      "products": [{"species name": "O", "coefficient": 2.0}]
    }
  ]
}
```

**Path:** `micm => micm_t("configs/v0/chapman", solver_type, error)`

### v1 Format (Modern - Single File)

Single YAML or JSON file with all definitions. CheMPAS-A's tracked mechanisms
under `micm_configs/` use YAML:

```yaml
version: "1.0.0"
name: LNOx-O3
species:
  - name: NO
    __molar mass: 0.030
    __initial concentration: 0.0
  - name: NO2
    __molar mass: 0.046
    __initial concentration: 0.0
  - name: O3
    __molar mass: 0.048
    __initial concentration: 0.0
phases:
  - name: gas
    species: [NO, NO2, O3]
reactions:
  - type: PHOTOLYSIS
    gas phase: gas
    reactants:
      - species name: NO2
        coefficient: 1
    products:
      - species name: NO
        coefficient: 1
      - species name: O3
        coefficient: 1
    name: jNO2
```

**Path:** `micm => micm_t("lnox_o3.yaml", solver_type, error)`

### Reaction Types

| Type | Description | Rate Source |
|------|-------------|-------------|
| `ARRHENIUS` | Temperature-dependent | Computed from A, B, C, D, E params |
| `PHOTOLYSIS` | Light-dependent | Via `rate_parameters` array |
| `USER_DEFINED` | External rate | Via `rate_parameters` array |
| `TROE` | Pressure-dependent | Computed internally |
| `TERNARY_CHEMICAL_ACTIVATION` | Three-body | Computed internally |

---

## Solver Types

```fortran
use musica_micm, only: Rosenbrock, RosenbrockStandardOrder, &
                       BackwardEuler, BackwardEulerStandardOrder, &
                       CudaRosenbrock
```

| Solver | Description | Maximum grid cells reported by the qualified build |
|--------|-------------|----------------------------------------------------|
| `Rosenbrock` | Vector-ordered Rosenbrock | Build-time vector group size (4) |
| `RosenbrockStandardOrder` | Standard-ordered Rosenbrock | Effectively unlimited |
| `BackwardEuler` | Vector-ordered implicit Euler | Build-time vector group size (4) |
| `BackwardEulerStandardOrder` | Standard-ordered implicit Euler | Effectively unlimited |
| `CudaRosenbrock` | GPU-accelerated vector ordering, when enabled | Solver-reported vector group size (4 by default) |

The vector size is a build option, so callers should query
`get_maximum_number_of_grid_cells()` instead of assuming 4. CheMPAS-A uses
`RosenbrockStandardOrder` because one state contains the complete
column-by-level product.

---

## Usage Patterns

### Single-Species Integration Skeleton

```fortran
subroutine run_o3_chemistry(dt, nCells, nLevels, T, P, rho_dry, qO3)
  use, intrinsic :: ieee_arithmetic, only: ieee_is_finite
  use iso_fortran_env, only: real64
  use musica_micm, only: micm_t, solver_stats_t, RosenbrockStandardOrder
  use musica_state, only: state_t
  use musica_util, only: error_t, string_t

  implicit none

  real(real64), intent(in) :: dt
  integer, intent(in) :: nCells, nLevels
  real(real64), intent(in) :: T(:,:), P(:,:), rho_dry(:,:)
  real(real64), intent(inout) :: qO3(:,:)

  real(real64), parameter :: R_GAS = 8.31446261815324_real64
  real(real64), parameter :: O3_MOLAR_MASS = 0.048_real64
  real(real64), parameter :: TIME_EPS_REL = 1.0e-9_real64
  integer, parameter :: MAX_SUB_CALLS = 100

  type(micm_t), pointer :: micm => null()
  type(state_t), pointer :: state => null()
  type(error_t) :: error
  type(string_t) :: solver_state
  type(solver_stats_t) :: stats

  integer :: total_cells, o3_micm_idx, cell_stride, var_stride
  integer :: iCell, k, micm_cell, idx, sub_call
  real(real64) :: elapsed, remaining, advanced

  if (dt <= 0.0_real64 .or. nCells < 1 .or. nLevels < 1) return
  if (size(T, 1) < nLevels .or. size(T, 2) < nCells .or. &
      size(P, 1) < nLevels .or. size(P, 2) < nCells .or. &
      size(rho_dry, 1) < nLevels .or. size(rho_dry, 2) < nCells .or. &
      size(qO3, 1) < nLevels .or. size(qO3, 2) < nCells) then
    write(*, '(A)') "Host arrays are smaller than nLevels by nCells"
    return
  end if
  if (any(T(:nLevels, :nCells) <= 0.0_real64) .or. &
      any(P(:nLevels, :nCells) <= 0.0_real64) .or. &
      any(rho_dry(:nLevels, :nCells) <= 0.0_real64)) then
    write(*, '(A)') "T, P, and rho_dry must be positive"
    return
  end if
  total_cells = nCells * nLevels

  ! Initialize
  micm => micm_t("lnox_o3.yaml", RosenbrockStandardOrder, error)
  if (.not. error%is_success() .or. .not. associated(micm)) then
    if (.not. error%is_success()) write(*, '(A)') error%message()
    go to 900
  end if

  state => micm%get_state(total_cells, error)
  if (.not. error%is_success() .or. .not. associated(state)) then
    if (.not. error%is_success()) write(*, '(A)') error%message()
    go to 900
  end if

  ! Get strides and species index
  cell_stride = state%species_strides%grid_cell
  var_stride = state%species_strides%variable
  o3_micm_idx = state%species_ordering%index("O3", error)
  if (.not. error%is_success()) then
    write(*, '(A)') error%message()
    go to 900
  end if

  ! Copy data to MICM state
  do iCell = 1, nCells
    do k = 1, nLevels
      micm_cell = (iCell - 1) * nLevels + k

      ! Set conditions
      state%conditions(micm_cell)%temperature = T(k, iCell)
      state%conditions(micm_cell)%pressure = P(k, iCell)
      state%conditions(micm_cell)%air_density = &
        P(k, iCell) / (R_GAS * T(k, iCell))

      ! Convert dry-air mass mixing ratio to concentration.
      idx = 1 + (micm_cell - 1) * cell_stride + &
        (o3_micm_idx - 1) * var_stride
      state%concentrations(idx) = &
        qO3(k, iCell) * rho_dry(k, iCell) / O3_MOLAR_MASS
    end do
  end do

  ! A successful solve may stop before dt after exhausting its internal-step
  ! budget. Resubmit the unadvanced duration and reject zero progress.
  elapsed = 0.0_real64
  sub_call = 0
  do while (dt - elapsed > TIME_EPS_REL * dt .and. sub_call < MAX_SUB_CALLS)
    sub_call = sub_call + 1
    remaining = dt - elapsed
    call micm%solve(remaining, state, solver_state, stats, error)
    if (.not. error%is_success()) then
      write(*, '(A)') error%message()
      go to 900
    end if

    advanced = stats%final_time()
    if (.not. ieee_is_finite(advanced) .or. advanced <= 0.0_real64) then
      write(*, '(A,A)') "MICM made no finite positive progress; solver state: ", &
        solver_state%get_char_array()
      go to 900
    end if
    elapsed = elapsed + advanced
  end do
  if (dt - elapsed > TIME_EPS_REL * dt) then
    write(*, '(A)') "MICM sub-call budget exhausted before reaching dt"
    go to 900
  end if

  ! Convert concentration back to dry-air mass mixing ratio.
  do iCell = 1, nCells
    do k = 1, nLevels
      micm_cell = (iCell - 1) * nLevels + k
      idx = 1 + (micm_cell - 1) * cell_stride + &
        (o3_micm_idx - 1) * var_stride
      qO3(k, iCell) = &
        state%concentrations(idx) * O3_MOLAR_MASS / rho_dry(k, iCell)
    end do
  end do

  ! Cleanup
900 continue
  if (associated(state)) deallocate(state)
  if (associated(micm)) deallocate(micm)

end subroutine
```

`o3_micm_idx` indexes only MICM's strided concentration storage. It must not be
used as an index into a host tracer array. CheMPAS-A separately resolves each
host field (for example, `index_qO3`) and keeps an explicit host-to-MICM species
mapping; a multi-species host should do the same.

### Grid Cell Indexing (MPAS to MICM)

```fortran
! MPAS: 2D grid (iCell, k) where iCell=1..nCells, k=1..nVertLevels
! MICM: 1D array with nCells*nVertLevels elements

! Forward mapping
micm_cell = (iCell - 1) * nVertLevels + k

! Reverse mapping
iCell = (micm_cell - 1) / nVertLevels + 1
k = mod(micm_cell - 1, nVertLevels) + 1
```

### Setting Rate Parameters (Photolysis)

```fortran
integer :: jO3_idx, cell_stride, var_stride, idx, micm_cell
real(real64), allocatable :: j_rate(:)

allocate(j_rate(total_cells))
! Populate j_rate(1:total_cells) in MICM cell order before assignment.

jO3_idx = state%rate_parameters_ordering%index("PHOTO.jO3", error)
cell_stride = state%rate_parameters_strides%grid_cell
var_stride = state%rate_parameters_strides%variable

do micm_cell = 1, total_cells
  idx = 1 + (micm_cell - 1) * cell_stride + (jO3_idx - 1) * var_stride
  state%rate_parameters(idx) = j_rate(micm_cell)
end do

deallocate(j_rate)
```

### Setting Rate Parameters (MIEM Emissions)

This subsection documents the extended emissions surface at the exact MUSICA
feature pin listed in [Supported Revision Scope](#supported-revision-scope),
not the smaller full-grid-only wrapper on audited MUSICA `main`.

CheMPAS-A constructs `mechanism_t(config_path,error)` and uses the selected
constructor on each rank:

```fortran
emissions => emissions_t(mechanism, global_nCells, nVertLevels, &
                         owned_indexToCellID, error, &
                         diagnostic_sectors=sectors, &
                         diagnostic_categories=categories, &
                         layered_diagnostics=layered, &
                         max_diagnostic_fields=field_cap)
```

Selected IDs are unique one-based inventory slots and output preserves caller
order. The legacy `emissions_t(mechanism,nCells,nVertLevels,error)` overload
requests a full grid for compatibility and equivalence tests; CheMPAS runtime
does not use it.

A single mechanism-configuration file can declare more than one inventory.
MIEM samples every configured source, requires consistent exact-grid metadata,
and returns the aggregated species buffers through this one `emissions_t`.
CheMPAS-A has exercised this with independent CAMS and FINN inventories and
with separate NOx and CH4 inventories.

After `emissions%run(epoch_seconds,dt_seconds,error)`, public C-owned pointers
are refreshed. `global_number_of_cells` remains the inventory dimension while
`number_of_cells` is selected/local. `surface_flux` contains column mass flux,
`layer_flux` contains species/level/selected-cell flux, and explicitly
requested `sector_flux`, `category_flux`, and layered group buffers are
available through their orderings. Storage is resolved with
`species_ordering%index(name,error)` plus the public cell/species/level
strides; iteration order is never treated as a storage index.

On the first successful selected run, `grid_metadata` exposes the global count,
ordered selected IDs, geometry, flags, optional sphere radius, fingerprint
algorithm/digest/manifest, `areaCell`, and every present cell-center coordinate
with units. The pointers remain owned by `emissions_t` and must not outlive or
be cached across `run()` calls. CheMPAS compares these fields with owned MPAS
geometry before applying a source.

MIEM species must cross-match writable MICM species and rate parameters named
`EMIS.<species>`. For every owned MPAS layer, CheMPAS-A converts the returned
layer flux into MICM's molar concentration tendency:

```fortran
dz = zgrid(k + 1, iCell) - zgrid(k, iCell)
rate = layer_flux_kg_m2_s / (dz * molar_mass_kg_mol)
```

The rate is written to the coupled state and, when
`config_chemistry_ref_solve = .true.`, the allocated reference state. The
formula preserves the sign: source-only species must be nonnegative, while
species explicitly listed in CheMPAS-A's `config_miem_net_flux_species` may be
positive upward exchange or negative uptake. That sign policy is a CheMPAS
host contract, not an additional argument to the MUSICA constructor. A surface
source has all upper-level layer fluxes zero; a normalized profile may populate
multiple levels and must close vertically to `surface_flux`. Dry-air density is
absent because division by `dz` converts mass per area to mass per volume
before division by molar mass. See
[MIEM_INTEGRATION.md](MIEM_INTEGRATION.md) for lifecycle, mapping, inventory,
and accounting contracts.

---

## Unit Conversions

MICM uses **mol/m³** for concentrations internally. All reaction rate parameters must be in compatible units.

### Reaction Rate Parameter Units

**Arrhenius reactions**
(`k = A * exp(C/T) * (T/D)^B * (1 + E*P)`):
- MICM computes `k` internally from the provided parameters
- Since concentrations are in mol/m³, `A` for bimolecular reactions must be in **m³/mol/s**
- Standard atmospheric chemistry uses cm³/molecule/s — you must convert:

```
A_micm [m³/mol/s] = A_atm [cm³/molecule/s] × Nₐ × 10⁻⁶
                   = A_atm × 6.022×10²³ × 10⁻⁶
```

| Reaction | A (cm³/molecule/s) | A (m³/mol/s) |
|----------|-------------------|--------------|
| NO + O3 → NO2 | 1.8×10⁻¹² | 1.084×10⁶ |

**Photolysis reactions**: Rate parameters (j-values) are set externally via
`state%rate_parameters` in **s⁻¹**. CheMPAS-A fills them from TUV-x when
`config_tuvx_config_file` is set. When that path is empty, a positive
`config_j_no2_max` enables the single-rate `cos(SZA)` fallback and requires
the mechanism parameter `PHOTO.jNO2`; when the path is empty and
`config_j_no2_max = 0`, CheMPAS-A drives no photolysis parameter. Before the
first enabled photolysis update, `PHOTO.*` parameters default to 0.

**Emission reactions**: `EMIS.<species>` parameters are molar concentration
tendencies in **mol m⁻³ s⁻¹**. MIEM supplies each layer's **kg m⁻² s⁻¹**, so
the conversion is `layer_flux / (layer_depth * species_molar_mass)`.

### MPAS to MICM

```fortran
! Dry-air mass mixing ratio [kg/kg dry air] to concentration [mol/m³]
! C = q × rho_dry / M_species

concentration = mixing_ratio * dry_air_density_kg_m3 / molar_mass_kg_mol
```

### MICM to MPAS

```fortran
! Concentration [mol/m³] to dry-air mass mixing ratio [kg/kg dry air]
! q = C × M_species / rho_dry

mixing_ratio = concentration * molar_mass_kg_mol / dry_air_density_kg_m3
```

### Air Density Conversion

```fortran
! MICM's environmental air_density is total moist molar density [mol/m³].
! CheMPAS-A derives it consistently from pressure and temperature.

real(real64), parameter :: R_GAS = 8.31446261815324_real64  ! J/mol/K

state%conditions(i)%air_density = pressure_pa / (R_GAS * temperature_k)
```

This environmental condition is distinct from the dry mass density used for
the two species conversions above. In CheMPAS-A, `rho_dry = zz * rho_zz`;
using a moist bulk mass density there would violate MPAS's dry-air MMR
convention.

### Common Molar Masses

| Species | Molar Mass [kg/mol] |
|---------|---------------------|
| Dry air | 0.0289644 |
| O₃ | 0.048 |
| O₂ | 0.032 |
| N₂ | 0.028 |
| H₂O | 0.018 |
| CO₂ | 0.044 |

---

## Related Documentation

- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - MPAS system architecture
- [MUSICA_INTEGRATION.md](MUSICA_INTEGRATION.md) - MPAS-MUSICA integration details
- [MIEM_INTEGRATION.md](MIEM_INTEGRATION.md) - MIEM public-API usage and workflow
- The installed, revision-qualified MUSICA-Fortran package discovered by
  `pkg-config`; sibling source trees are inspection references only
