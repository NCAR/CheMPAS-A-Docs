# Chapter 8: Chemistry Coupling

This chapter documents the runtime chemistry coupling between MPAS and the
MUSICA stack — MICM (chemistry solver) and TUV-x (photolysis solver) — as
implemented in `src/core_atmosphere/chemistry/`. The chapter assumes the
runtime tracer infrastructure described in [Chapter 7](07-runtime-tracers.md);
namelist details are in Appendix B. For the upstream chemistry-package
documentation see <https://musica.readthedocs.io/>,
<https://micm.readthedocs.io/>, and <https://tuv-x.readthedocs.io/>.

## 8.1 Overview

The chemistry pipeline lives in `src/core_atmosphere/chemistry/` and consists
of eight Fortran modules:

| Module | File | Role |
|--------|------|------|
| `mpas_atm_chemistry`  | `mpas_atm_chemistry.F`        | Init/step/finalize driver, transactional gather/solve/scatter, runtime diagnostics |
| `mpas_chem_constants` | `mpas_chem_constants.F`       | Shared physical constants and unit conversions |
| `mpas_musica`         | `musica/mpas_musica.F`        | MICM solver instance, coupled state, optional reference state, species table, unit conversion, photolysis rate parameters |
| `mpas_miem`           | `musica/mpas_miem.F`           | Selected-cell MIEM bridge, exact-grid validation, diagnostic selection, mass accounting |
| `mpas_tuvx`           | `mpas_tuvx.F`                 | TUV-x setup with from-host height grid, air/T/O3/O2 profiles, and cloud radiator |
| `mpas_prescribed_fields` | `mpas_prescribed_fields.F` | Exact-grid validation, selected-cell reads, cyclic monthly interpolation, and two-slab O3 caching |
| `mpas_solar_geometry` | `mpas_solar_geometry.F`       | Spencer (1971) per-cell `cos(SZA)` |
| `mpas_lightning_nox`  | `mpas_lightning_nox.F`        | Vertical-velocity-gated NO source |

The driver is `chemistry_step`, called once per
MPAS dynamics step after physics updates time level 1 and before dynamics
advances the transported state. Its active chemistry work is operator-split
into these phases:

1. Chemistry interval gate, controlled by `config_chemistry_interval`.
2. Optional photolysis-rate update (TUV-x or `cos(SZA)` fallback), gated by
   `config_tuvx_update_interval`.
3. Optional MIEM inventory sampling and conversion of surface/layer fluxes to
   writable `EMIS.*` rate parameters.
4. Lightning NOx injection into `qNO` (no-op when the mechanism does not
   include `qNO`).
5. MPAS → MICM state gather, with conversion to mol m⁻³.
6. MICM solve, optionally split into `config_chem_substeps` sub-steps, with
   an optional uncoupled reference solve in parallel.
7. MICM → MPAS state scatter, with conversion back to mass mixing ratio.
8. Successful-step publication of photolysis/emissions diagnostics and MIEM
   mass accounting. Recoverable gather/solve/scatter failures restore the
   pre-step tracer snapshot and are fatal after
   `config_chem_max_failures` consecutive failures.

Every routine that touches MICM is wrapped in `#ifdef MPAS_USE_MUSICA`, so
the entire chemistry pipeline compiles out without the `MUSICA=true` build
flag (see [Section 3.10](03-building.md#310-build-chempas-a-and-verify-the-musica-link)).

## 8.2 Initialization

`chemistry_init` drives chemistry startup, in order:

1. Read the `&chemistry`, `&emissions`, `&photolysis`, and `&lnox` namelist
   records (paths, emissions selection, lightning NOx, TUV-x, solver controls,
   solar geometry, and failure policy). Chemistry requires one MPAS block per
   MPI task.
2. `musica_init` — instantiate the persistent
   `micm_t` solver from `config_micm_file` using the Rosenbrock standard
   ordering, allocate the coupled `state` and, only when
   `config_chemistry_ref_solve = .true.`, `state_ref`; populate the
   `chem_species` table from MICM's species ordering; read each species'
   `__molar mass` and `__initial concentration` properties; and seed every
   allocated state.
3. When `config_miem_file` is nonempty, initialize MIEM for only the ordered
   rank-owned `indexToCellID` values. Capture and validate the host global/local
   dimensions, selected IDs, and supplied MPAS geometry arrays; prepare bounded
   sector/category diagnostics; configure signed net-flux species; and match
   each inventory species to a writable `EMIS.<species>` MICM parameter. The
   inventory metadata are not available until the first successful `miem_run`,
   when its exact-grid identity and geometry are compared with the captured
   MPAS values before any source is applied. An empty path is a deliberate
   no-op.
4. `resolve_mpas_indices` — for each MICM
   species name `X`, look up the MPAS scalar index from the pool dimension
   `index_qX`. The MPAS tracer pool was already extended at startup by
   the runtime-var callback registered during `atm_generate_pools`
   (Chapter 7).
5. `chemistry_lightning_nox_init` — read
   `config_lnox_*`; remains a no-op when `qNO` is not in the mechanism.
6. Initialize the selected upper-column mode. `legacy_static` reads the
   existing one-dimensional CSV. `spatial_climatology` opens an exact-grid
   monthly NetCDF package, validates its mesh/calendar/units, and retains only
   the two active monthly O3 slabs for rank-owned cells.
7. `tuvx_init` — register from-host grids and profiles,
   optionally extend the column with the selected upper-atmosphere input,
   construct the TUV-x solver against a 102-bin CAM wavelength grid, and
   cache every photolysis reaction TUV-x reports. Skipped when
   `config_tuvx_config_file` is empty.
8. `musica_cache_photo_indices` — for every
   reaction name TUV-x cached (or the single fallback name `jNO2`), look up
   `PHOTO.<name>` in MICM's `rate_parameters_ordering` and store the stride
   index for later writes.
9. Only after all chemistry, emissions, photolysis, and prescribed-field
   configuration has passed, copy MICM's initial state to MPAS when the input
   file did not already initialize spatially varying chemistry. Zero the
   initial runtime diagnostics before the first history write.

`assign_rate_parameters` in `mpas_musica.F` populates MICM's
`rate_parameters` array at `musica_init` time. By convention, `USER.*`
parameters default to `1.0` so the YAML mechanism's `scaling_factor`
defines the effective rate; `PHOTO.*` parameters default to `0`. The
pseudo-first-order NOx loss parameters whose names begin with `LOSS.` are
wired to `1 / config_lnox_nox_tau` when that namelist value is positive.

Module-level state cached at init, used by `chemistry_step`:

- Solar geometry: `chem_lat`, `chem_lon`, `chem_use_grid_coords`,
  `chem_j_no2_max`.
- TUV-x update interval: `tuvx_update_interval`, `tuvx_time_since_last`.
- Chemistry solve interval: `chemistry_interval`,
  `chemistry_interval_clock`, `chemistry_accumulated_dt`.
- TUV-x activation and tracer indices: `use_tuvx`, `idx_qO3`, `idx_qc`,
  `idx_qr`.
- MICM controls: `chem_substeps_val`, `micm_relative_tolerance_val`,
  `use_ref_solve`, `chem_max_consecutive_failures`.

## 8.3 The Chemistry Time Step

`chemistry_step(dt, currTime, mesh, state, diag, dimensions, time_lev)`
is the per-step entry point.

**Phase 0 — Chemistry interval gate.** `config_chemistry_interval = 0.0`
runs chemistry every MPAS step. Positive values accumulate elapsed dynamics
timesteps at entry; when the accumulated clock is still below the interval,
`chemistry_step` returns before photolysis, emissions, lightning NOx, and MICM
work. When the interval fires, MIEM sampling, LNOx injection, and the MICM
solve use the accumulated chemistry timestep.

**Phase 1 — Photolysis update.** A module accumulator
`tuvx_time_since_last` tracks simulated seconds since the photolysis block
last fired. When the accumulator reaches `config_tuvx_update_interval`,
the block fires:

- Compute per-cell `cos(SZA)` (broadcast from `config_chemistry_latitude`/
  `_longitude` when `config_chemistry_use_grid_coords = .false.`, otherwise
  per-cell from `latCell`/`lonCell`).
- Allocate `photo_rates(n_rates, nVertLevels, nCells)` and either
  call `tuvx_compute_photolysis` per cell or fill the single-rate fallback
  `jNO2 = j_max * max(0, cos(SZA))`.
- Write the rates into MICM via `musica_set_photolysis_rates`. The diagnostic
  fields and cadence clock are committed only after the complete chemistry
  transaction succeeds.

On skipped steps the accumulator just ticks forward and MICM keeps using
the rates last written. Setting `config_tuvx_update_interval = 0` (the
default) updates every chemistry step. In `spatial_climatology` mode, the same
block updates the two-slab monthly O3 interpolation for the rank-owned cells
before extending each TUV-x column.

**Phase 2 — MIEM sampling.** When emissions are enabled, MIEM is called once
for the accumulated chemistry interval. It returns column and layer fluxes in
the owned MPAS-cell order, plus any requested sector/category diagnostics.
`musica_set_emission_fluxes` converts the layer mass fluxes to MICM
concentration tendencies and writes the matching `EMIS.*` rate parameters in
the coupled state and, when enabled, the allocated reference state. These rates
remain fixed across chemistry substeps. Negative values are accepted only for
species named by `config_miem_net_flux_species`; all other inventory values are
source-only.

**Phase 3 — Lightning NOx injection.** `lightning_nox_inject` modifies
`scalars(idx_qNO, :, :)` in place.
Operator-split: the increment is added before the MICM call, not as a
tendency. MIEM and parameterized lightning may both supply NOx, so inventories
that already include lightning can double count it.

**Phase 4 — MPAS → MICM gather.** `chemistry_from_MPAS` reconstructs
per-cell ρ, T, and p (Section 8.4), then calls `MICM_from_chemistry`, which
writes MICM's `state%conditions` and converts each species' mixing ratio to
mol m⁻³. Immediately before LNOx and gather, the driver snapshots only the
active chemistry-species rows of the MPAS scalar pool.

**Phase 5 — MICM solve.** The chemistry timestep is divided into
`config_chem_substeps` calls to `musica_step`, each advancing the coupled state
by `dt_chem / N`. TUV-x and MIEM rate parameters remain frozen across these
substeps. When `config_chemistry_ref_solve = .true.`, `musica_step_ref` runs in
lockstep on the reference state.

**Phase 6 — MICM → MPAS scatter.** `chemistry_to_MPAS` reconstructs ρ and
calls `MICM_to_chemistry`, which converts the integrated mol m⁻³ state back
to mass mixing ratio and writes it into the scalars pool at `time_lev`.

**Phase 7 — commit or rollback.** After a successful scatter, MIEM integrates
the exact applied fluxes over owned-cell area and timestep, emissions and
photolysis diagnostics are published, cadence clocks advance, and the
consecutive-failure counter resets. A recoverable gather or solver failure
restores the MPAS chemistry snapshot, discards uncommitted diagnostics and
MIEM mass, rewinds the photolysis cadence, and forces the optional reference
state to re-synchronize on the next successful step. The next gather refreshes
the coupled MICM state from MPAS. After `config_chem_max_failures` consecutive
failures, the model aborts instead of continuing indefinitely.

The phases are wrapped in MPAS timer regions: `chemistry`, `chem MPAS->MICM`,
`chem MIEM`, `chem MICM solve`, `chem MICM ref solve` (when enabled), and
`chem MICM->MPAS`. They appear in the standard MPAS performance log.

## 8.4 State Transfer

MPAS stores chemistry tracers in the `scalars` pool as dry-air mass mixing
ratio (kg of species per kg of dry air). MICM works in volumetric concentration
(mol m⁻³). Conversion happens once per direction per chemistry step.

**Air state reconstruction.** `chem_env_fill` computes:

- ρₑ = `zz` × `rho_zz` [kg of dry air m⁻³]
- T = (`theta_m` / (1 + Rv/Rd × qv)) × `exner` [K]
- p = `pressure_p` + `pressure_base` [Pa]

When the pressure fields are unavailable, the fallback is
`p = ρₑ Rd T (1 + Rv/Rd × qv)`. These per-cell, per-level values feed
`state%conditions(:)%temperature` and `%pressure`. MICM's
`%air_density` condition is the total moist molar density `p / (R T)`;
species MMR/concentration conversion separately uses ρₑ because MPAS
scalars are dry-air mass mixing ratios.

**MICM cell layout.** MICM's working state is a flat array indexed by a
single grid-cell index that runs over the full (column, level) product:
`micm_cell = (iCell - 1) * nVertLevels + k`.
Per-species concentration storage is
`1 + (micm_cell - 1) * cell_stride + (micm_index - 1) * var_stride`,
where the strides are read from `state%species_strides` and the species
indices come from `state%species_ordering`.

**Forward conversion** (`MICM_from_chemistry`):

```
conc[mol m⁻³] = q[kg/kg] · ρ[kg/m³] / M[kg/mol]
```

`M` (the species molar mass) is read once at init from the MICM property
`__molar mass` and cached in `chem_species(:)%molar_mass`.

**Reverse conversion** (`MICM_to_chemistry`):

```
q[kg/kg] = conc[mol m⁻³] · M[kg/mol] / ρ[kg/m³]
```

The same ρ cache is used in both directions; `MICM_to_chemistry` does not
re-compute T or p — only concentrations are scattered back.

`micm_to_mpas_chem` is a seed-only variant
used by `chemistry_seed_chem` to broadcast each species' MICM initial
concentration across all MPAS columns at startup. It does not write
environmental conditions.

## 8.5 Chemistry Tracer Output Units

The authoritative chemistry state is always the dry-air mass mixing ratio in
`q<MICM-species-name>`. Those fields remain the inputs to transport and MICM,
are the only chemistry fields read from input or written automatically to
restart streams, and retain units of `kg kg^{-1}`.

Two `&chemistry` options can add volume-mixing-ratio companions to history
output:

```fortran
config_chem_tracer_output_unit = 'ppbv'
config_chem_tracer_output_overrides = 'O3=ppmv,NO=ppbv,NO2=ppbv,H2O=fraction,AB=mmr'
```

`config_chem_tracer_output_unit` applies to every species in the MICM
configuration. Its default is `mmr`, which preserves the existing output and
does not create any companion fields. The accepted values are `mmr`,
`fraction`, `percent`, `ppmv`, `ppbv`, and `pptv`; unit names are
case-insensitive.

`config_chem_tracer_output_overrides` is a comma-separated list of
`SPECIES=UNIT` mappings. Species names use the exact, case-sensitive names in
the MICM configuration, without the MPAS `q` prefix. An override takes
precedence over the global selection. Setting a species to `mmr` suppresses
its VMR companion under a non-MMR global selection. Unknown or duplicate
species, malformed mappings, and unsupported units are startup errors.

A non-MMR selection creates an output-only diagnostic named
`vmr_<MICM-species-name>`. Immediately before output, it is filled from the
current mass mixing ratio:

```text
vmr_output = q * M_air / M_species * unit_scale
```

where `M_air = 0.0289644 kg mol^{-1}`, `M_species` is read from the MICM
configuration, and `unit_scale` is 1 for `fraction`, 10² for `percent`, 10⁶
for `ppmv`, 10⁹ for `ppbv`, or 10¹² for `pptv`. NetCDF units are respectively
`mol mol^{-1}`, `percent`, `ppmv`, `ppbv`, and `pptv`.

The diagnostics are automatically added to mutable output streams that contain
`scalars`. They are not added to immutable input/restart streams, do not enter
the `scalars` pool, and never modify the transported state. A custom mutable
stream may also list a `vmr_*` field explicitly. Host-bound MICM species are
handled the same way: for example, `vmr_H2O` is derived from the existing MPAS
`qv` field rather than from a new `qH2O` constituent. Fixed dry-air host
parameters are handled explicitly: when mechanism metadata host-binds O2 or N2
to the fixed dry-air fractions used by the coupler, `vmr_O2` or `vmr_N2` is
filled from that same fixed fraction and not from the `qv` index anchor.

## 8.6 Photolysis

Photolysis rates are external rate parameters from MICM's perspective:
MICM does not solve photolysis itself but reads
`state%rate_parameters(PHOTO.<name>)` for every photolysis reaction.
CheMPAS-A supplies these from one of two sources, set per build/run by
the namelist.

**TUV-x with from-host atmosphere and cloud radiator** (preferred). When
`config_tuvx_config_file` is non-empty, `tuvx_init` in `mpas_tuvx.F`
constructs the solver using:

- A from-host height grid in km, sized for the composite column (MPAS
  layers + optional extension layers).
- From-host air, temperature, O3, and O2 profiles in molecule cm⁻³.
- A cloud radiator on a 102-bin CAM wavelength grid.

`tuvx_init` enumerates every photolysis reaction the JSON config declares,
caches the names and stride indices in `photo_names`/`tuvx_indices`, and
hands the same name list to `musica_cache_photo_indices` so MICM and TUV-x
agree on the reaction set.

`tuvx_compute_photolysis` runs once per cell per update:

1. Build the composite column = MPAS layers + extension layers.
2. Convert MPAS mid-layer values to TUV-x units (number density in
   molecule cm⁻³, layer densities in molecule cm⁻²).
3. Update the from-host profiles (`air_profile%set_*`, `temp_profile`,
   `o3_profile`, `o2_profile`) and call
   `air_profile%calculate_exo_layer_density(7.0_dk, ...)` to populate the
   above-top layer for spherical-geometry slant-path computations.
4. Compute per-layer cloud optical depth and write it to the cloud
   radiator's `set_optical_depths`. Single-scattering albedo (0.999999)
   and asymmetry parameter (0.85) are constants.
5. Call `tuvx_solver%run(sza_rad, esd, photo_rates, heating_rates, ...)`.
6. Average TUV-x's edge-defined rates to mid-layer values for the MPAS
   slice; extension-layer rates are computed but discarded.
7. Skip the TUV-x call entirely at night (cos(SZA) ≤ 0) and return zeros.

**Solar zenith angle.** `solar_cos_sza` in `mpas_solar_geometry.F`
implements the Spencer (1971) declination + equation-of-time formula.
With `config_chemistry_use_grid_coords = .true.`, every cell uses its
own `latCell`/`lonCell`; otherwise all cells share the namelist
`config_chemistry_latitude` and `config_chemistry_longitude`, intended for
idealized cases where solar geometry should be uniform across the domain.

**Cloud optical depth.** `compute_cloud_optical_depth`
in `mpas_tuvx.F` uses

```
τ = 3 · LWC · dz / (2 · r_eff · ρ_water)
```

with `r_eff = 10 µm` for cloud water (`qc`) and `r_eff = 500 µm` for rain
water (`qr`). LWC is reconstructed from `q · ρ_dry` in each layer because the
MPAS water scalars use the dry-air mass convention. The
total τ is the sum of cloud and rain contributions; by the choice of
`r_eff`, rain contributes ~50× less per unit mass than cloud water.

**Upper-atmosphere column extension.** `config_tuvx_upper_column_mode`
selects exactly one of `none`, `legacy_static`, or `spatial_climatology`.
The legacy mode reads `(z_km, T_K, n_air_cm⁻³, n_O3_cm⁻³)` edge values from
`config_tuvx_extension_file`. The spatial mode reads
`chempas-prescribed-field-package-v1` from
`config_tuvx_prescribed_field_file`; the package supplies monthly O3 number
density on the exact MPAS mesh while the frozen reference atmosphere supplies
height, temperature, air, and O2 structure. Monthly values are linearly
interpolated between Gregorian month-midpoint anchors with a cyclic
December-to-January bracket. Only prognostic MPAS O3 is used at and below the
model top, and prescribed O3 is used strictly above it. The model top must
match the package's first edge within 0.5 m. Neither provider accepts or
modifies prognostic `qO3`.

`config_tuvx_top_extension` remains a compatibility consistency flag and must
be `.true.` for either extension mode and `.false.` for `none`. Ambiguous
combinations, a non-Gregorian spatial run, missing variables, wrong units,
invalid coordinates, or a mesh mismatch are fatal during initialization.

**Single-rate fallback.** When `config_tuvx_config_file` is empty and
`config_j_no2_max > 0`, the driver uses
`jNO2 = config_j_no2_max · max(0, cos(SZA))`, filling slot 1 of `photo_rates`.
The MICM mechanism must then declare `PHOTO.jNO2` for
`musica_cache_photo_indices` to wire up; otherwise `chemistry_init` aborts.
When the TUV-x path is empty and `config_j_no2_max = 0`, the driver caches and
drives no photolysis parameter, and the mechanism need not declare
`PHOTO.jNO2`.

**Update interval.** `config_tuvx_update_interval` gates the entire
photolysis block in seconds. The default (0) updates every chemistry
step; positive values hold rates between updates and MICM reuses the
last-set values. Useful when TUV-x dominates the chemistry-step cost
and rates change slowly relative to the MPAS dt.

## 8.7 Lightning NOx

`mpas_lightning_nox.F` is a stand-alone source-only module. It injects `qNO`
mass mixing ratio where layer-midpoint vertical velocity exceeds a threshold,
using one of two gates: the default `altitude` mode applies a fixed MSL-height
window and updraft-scaled rate, while `isotherm` mode applies a mixed-phase
temperature window and constant configured rate. The chemistry response
(NO + O3 → NO2, NO2 + hν → NO + O3) is handled by MICM.

`lightning_nox_init` looks up `index_qNO` in
the scalars pool. If `qNO` is not in the active mechanism (e.g., the
ABBA coupling-test mechanism), the module sets `lnox_active = .false.` and
the inject hook becomes a no-op. A nonpositive `config_lnox_source_rate` or
`config_lnox_w_ref` currently disables either mode. `config_lnox_w_ref` enters
only the altitude-mode formula, but the current initializer validates it before
the mode-specific branch and therefore still requires it to be positive for
isotherm mode.

`lightning_nox_inject` is called from
`chemistry_step` before the MPAS → MICM gather (operator-split, not a
tendency). For each (cell, level) pair:

- Layer-mid w = ½ · (`w(k)` + `w(k+1)`).
- Layer-mid z = ½ · (`zgrid(k)` + `zgrid(k+1)`), using MPAS height
  above MSL, not AGL.
- Layer-mid temperature is supplied from the chemistry environment for
  isotherm mode.

Altitude mode uses:

```
Δq = config_lnox_source_rate · max(0, w_mid - config_lnox_w_threshold) / config_lnox_w_ref
     · dt_chem · 1e-9 · (M_NO / M_AIR)
```

and requires `config_lnox_z_min ≤ z_mid ≤ config_lnox_z_max`.
Isotherm mode uses:

```
Δq = config_lnox_source_rate · dt_chem · 1e-9 · (M_NO / M_AIR)
```

and requires `config_lnox_t_min ≤ T_mid ≤ config_lnox_t_max`. Both modes
also require `w_mid > config_lnox_w_threshold`.

In both equations, `1e-9` converts ppbv to mole fraction and `M_NO / M_AIR` ≈
0.030 / 0.029 (kg mol⁻¹) converts mole fraction to mass mixing ratio.
Over terrain, the altitude-mode injection slab stays fixed in MSL coordinates
and does not follow the surface. The source is a mixing-ratio rate
(ppbv s⁻¹), so total injected moles scale with the air mass in each
gated cell and domain-integrated production is resolution-dependent on
variable meshes. These semantics follow the DC3 parcel-model design in
`LNOx.md` and are intended for flat-terrain idealized cases; recalibrate
before applying them to terrain-following or variable-resolution
applications. Isotherm mode follows the configured thermal layer but retains
the same air-mass/resolution caveat. With the default
`config_lnox_source_rate = 0`, the entire injection is disabled.

## 8.8 Solver Controls

Five namelist options shape MICM's per-step behavior and failure policy. They
control the cadence, accuracy, work subdivision, optional reference solve, and
failure policy of the production `RosenbrockStandardOrder` solver. Stiff or
fast-transient mechanisms may require smaller outer substeps or tighter error
tolerances.

**`config_chemistry_interval`** (default 0.0 s). The default runs chemistry
every MPAS step. Positive values accumulate elapsed dynamics timesteps and
skip the chemistry body until the interval is reached; the next MIEM sampling,
LNOx injection, and MICM solve use the accumulated chemistry timestep.

**`config_chem_substeps`** (default 1). Each fired chemistry interval is divided
into N outer substeps and `musica_step` is called N times with
`dt_chem / N`. Photolysis and emissions rates are set once per fired interval
and frozen across `config_chem_substeps`.

**`config_micm_relative_tolerance`** (default 1e-6, MICM's own default).
Tightening (e.g., to 1e-9) forces MICM's adaptive controller to subdivide
its internal steps more aggressively before accepting a step. Passed to
`musica_init` and applied at solver-state construction.

**Re-entrant solve loop.** `musica_step` wraps `micm%solve` in a sub-call loop
with `MAX_SUB_CALLS = 100`. MICM's
adaptive controller has its own internal step budget
(`max_number_of_steps`, default 1000 for the qualified Rosenbrock solver) and
returns early when it exhausts
that budget without reaching the requested interval. The wrapper inspects
`solver_stats%final_time()`, computes the remaining duration, and
resubmits until the full interval is covered. It aborts if MICM advances
0 s on any sub-call (genuine stall) or if the 100-sub-call cap is hit.
This pattern is borrowed from MUSICA-Fortran's `column_model.F90` example
and is required for stiff transients (e.g., Chapman chemistry at sunrise).

**Reference solve.** When `config_chemistry_ref_solve = .true.`,
`musica_step_ref` runs in lockstep on
`state_ref`, an independent MICM state seeded once from the coupled state on
the first chemistry step by `copy_state_to_ref`. The reference state is not
coupled to MPAS: it sees the same photolysis and MIEM rate parameters and the
same time step, but no subsequent advection, per-step environmental updates,
or operator-split LNOx injections. Divergence is therefore a chemistry-only
reference comparison that includes transport plus those omitted coupling and
source effects; it is a pure transport attribution only when the other inputs
are static or absent. The reference solve doubles chemistry cost and is off by
default.

**`config_chem_max_failures`** (default 3). A failed environment gather or
MICM transfer/solve increments a consecutive-failure counter. Recoverable
failures leave MPAS tracers and step-time diagnostics at their last successful
state. A successful chemistry transaction resets the counter; reaching the
configured positive limit is fatal. This setting is a guardrail, not a reason
to ignore recurring solver errors.

## 8.9 Diagnostics and Logging

**Photolysis diag fields.** At setup, CheMPAS-A queries the TUV-x
configuration for its photolysis reaction names and injects matching
`j_<reaction>` diagnostic fields into the diag pool. The fallback
`config_j_no2_max` path injects only `j_jNO2`. `chemistry_set_photolysis_diag`
(`mpas_atm_chemistry.F`) writes the cached photolysis-rate array into those
runtime fields after every photolysis update, and logs a critical error if an
expected field is missing.

Because the `j_<rate>` fields are injected at runtime from the active TUV-x
mechanism's rate names (or `j_jNO2` for the `cos(SZA)` fallback when
`config_j_no2_max > 0`) rather than declared in the Registry, they must be named
explicitly to be written to history: list the exact `j_<rate>` field names (e.g.
`j_jNO2`) in `stream_list.atmosphere.output`. They only exist when chemistry
with photolysis is configured, so remove any `j_<rate>` entries when running
without chemistry to avoid stream-manager warnings.

**MIEM emissions fields.** A nonempty `config_miem_file` makes CheMPAS-A query
writable `EMIS.<species>` parameters from the separate MICM mechanism and
inject `emis_<species>` column-flux fields at setup. Each MPI rank constructs
MIEM with only its ordered owned `indexToCellID` values, reads coalesced
inventory hyperslabs, and validates returned area/geometry metadata before the
first source is applied. A source may inject at the surface or use a fixed
normalized profile with one weight per model level; all populated layer rates
are set in the coupled MICM state and, when enabled, the allocated reference
state, then frozen across chemistry substeps.

Explicit `config_miem_diagnostic_sectors` and
`config_miem_diagnostic_categories` lists add bounded disaggregated fields.
`config_miem_layered_diagnostics = .true.` also adds
`emis_<species>_layer` and `_layer` forms of requested groups. The
`config_miem_max_diagnostic_fields` cap is checked before runtime-field
allocation. Column, group, layer, finalize-log, and (for emissions-only
mechanisms) tracer-mass closure are exercised by the tracked R6 case. See the
[MIEM workflow](../chempas/musica/MIEM_INTEGRATION.md) for exact names, units,
accounting equations, and the no-runtime-regridding contract.

**MICM solver statistics.** `log_solver_stats`
in `mpas_musica.F` emits MICM's per-step counters: function
calls, Jacobian updates, total internal steps, accepted and rejected
steps, LU decompositions, linear solves, and the final time the solver
reached. Logged after every `musica_step` outer call.

**Re-entrant sub-call summary.** `musica_step` logs a single line when
MICM completed the requested interval in more than one sub-call,
indicating the adaptive controller's internal budget was exhausted but
the wrapper recovered. Recurring sub-call activity is a signal to
tighten `config_micm_relative_tolerance` or raise
`config_chem_substeps`.

**Coupled vs reference column comparison.** When
`config_chemistry_ref_solve = .true.`, `log_column_comparison`
is called from `chemistry_step` after each
MICM solve. For a probe cell (`nCells / 2`), it logs coupled and
reference concentrations every `nVertLevels / 4` levels for every
species. Differences quantify advection effects.

**Per-species seed log.** `micm_to_mpas_chem`
logs `min`/`max` of each tracer after the initial-state seed, and the
species-table init in `musica_init` logs each species' resolved molar
mass.

For full namelist documentation including units and default values, see
Appendix B.
