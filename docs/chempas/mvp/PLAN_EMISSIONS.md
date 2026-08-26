# MIEM Emissions Integration Implementation Plan

**Status:** Phases 0-9 complete; final Phase 9E checkpoint pushed and remote-verified

**Target branch:** `develop_emissions`

**Planning baseline:** `4eb4e677` (`develop_emissions` matched `develop_fable` when this plan was written)

**Primary dependency:** An exact, recorded MUSICA commit exposing the `musica_emissions` Fortran API. Package version `0.16.5` is the minimum observed API level, but the version string alone is not a reproducible pin because untagged MUSICA revisions can report the same version.

**Preflight correction:** 2026-08-05; dependency closure, planar-mesh identity, chem-box asset provenance, diagnostic discovery, and disabled-path baselines were re-audited before implementation.

## Goal

Add optional offline surface emissions to CheMPAS-A through the MUSICA MIEM Fortran API. MIEM will read time-dependent inventory fluxes, CheMPAS-A will map the global inventory cells to rank-owned MPAS cells, and MICM `EMIS.<species>` reactions will apply the fluxes continuously during the chemistry solve.

The first implementation is complete when:

- an empty `config_miem_file` preserves the current no-emissions behavior;
- emissions inventories are preprocessed onto the exact global MPAS mesh and cell order;
- MIEM fluxes are mapped correctly on one or many MPI ranks;
- surface fluxes are converted to MICM volumetric source rates with correct units;
- only the lowest MPAS layer receives the source rate;
- the coupled and optional reference MICM states receive identical emissions forcing;
- per-species surface-flux diagnostics are available in MPAS output;
- mass, time interpolation, restart, mapping, and failure-path tests pass; and
- the documented MUSICA build and runtime workflows work with an 8-rank CheMPAS-A smoke test; and
- every completed phase, stage, and separately reported milestone has a verified commit pushed to the target branch.

## Settled Phase 1 decisions

- **Spatial remapping happens before the MPAS run.** MIEM Phase 1 does not regrid inside CheMPAS-A.
- The inventory is one **global** file, not one file per MPI rank.
- Inventory cell slot `j` is the MPAS cell whose global `indexToCellID` is `j`.
- The inventory `nCells` dimension must equal the global MPAS cell count.
- Mesh identity is geometry-aware. Spherical meshes use `latCell`/`lonCell`; planar meshes use `xCell`/`yCell`/`zCell`. All-zero planar latitude/longitude arrays are never accepted as proof of identity.
- The preprocessing workflow must validate geometry, coordinates, global IDs, and order, not only `nCells`.
- The canonical 64-cell chem-box mesh, initialized state, and 8-rank partition are repository-controlled test assets with recorded hashes and a pinned regeneration recipe.
- Each MPI rank constructs a full-grid MIEM object and selects its owned cells after each MIEM call. This intentionally trades replicated I/O and memory for correctness with the current API.
- Construct `emissions_t` with `n_vert_levels=1`; MIEM Phase 1 supplies only a surface flux.
- The only new runtime switch is `config_miem_file`. An empty string disables MIEM. There is no separate enable flag or MIEM update cadence in Phase 1.
- MIEM runs once per chemistry solve. Its rates remain fixed across `config_chem_substeps`.
- MIEM species names must map exactly to MICM species and to MICM rate parameters named `EMIS.<species>`.
- Runtime diagnostic names are discovered from `config_micm_file` only when `config_miem_file` enables MIEM. The MIEM configuration is not a chemistry-mechanism species source.
- Species splitting and scaling, such as a 9:1 NO:NO2 split, belong in the MIEM emissions configuration rather than CheMPAS-A code.
- Existing lightning NOx remains a separate volumetric source. MIEM does not replace it.
- Only the Gregorian calendar is supported when MIEM is enabled.
- Deterministic MIEM configuration, inventory, mapping, calendar, or time-coverage errors are fatal. Configured emissions must not silently disappear.

## Delivery checkpoint discipline

Implementation proceeds through repository checkpoints, not an unpushed accumulation of work:

- Before starting a phase, stage, or separately reported milestone, define its scoped files and verification command.
- When that checkpoint is complete, run its local tests and `git diff --check`, stage only its scoped changes, make a focused commit, and push `develop_emissions` before beginning the next checkpoint.
- Record the local commit SHA, remote branch, verification command, and result in the implementation log or pull-request notes. Confirm the pushed remote SHA matches the local checkpoint.
- A phase gate requires all internal stage/milestone commits to be pushed. The final stage commit may also be the phase checkpoint when it is made after the phase gate passes; otherwise update the scoped checkpoint record and make a final phase commit. Do not use an unverified earlier commit as the phase checkpoint.
- A failed push is a delivery blocker for advancing to the next checkpoint. Do not rewrite or squash already pushed checkpoints unless explicitly authorized.
- Preserve unrelated user changes and generated run data outside every checkpoint.

## Phase 1 scope and non-goals

Phase 1 supports:

- MIEM offline sources;
- MIEM UPTEMPO and ECCAD readers as exposed by the installed API;
- temporal interpolation selected in the MIEM configuration;
- surface injection into MPAS level 1; and
- exact-grid global inventories.

Phase 1 does not include:

- runtime horizontal regridding;
- generic scientific remapping-method selection inside CheMPAS-A;
- online or meteorology-dependent emissions;
- elevated, plume-rise, or multi-level injection;
- rank-local inventory reads or distributed MIEM state;
- climatological wraparound outside the inventory time range;
- sector-resolved MPAS diagnostics;
- changing or replacing the existing lightning-NOx implementation; or
- restart persistence for the existing nonzero chemistry-cadence accumulator.

## Existing integration points

| Concern | Current location | Planned extension |
|---|---|---|
| Chemistry lifecycle and orchestration | `src/core_atmosphere/chemistry/mpas_atm_chemistry.F` | Initialize, run, diagnose, and finalize MIEM |
| MICM state and rate parameters | `src/core_atmosphere/chemistry/musica/mpas_musica.F` | Cache and set `EMIS.*` parameters |
| MIEM ownership | New `src/core_atmosphere/chemistry/musica/mpas_miem.F` | Own MUSICA mechanism/emissions objects and global-to-local flux selection |
| Build ordering | `src/core_atmosphere/chemistry/musica/Makefile` and parent chemistry `Makefile` | Compile and archive `mpas_miem.o` before the chemistry interface |
| Namelist | `src/core_atmosphere/Registry.xml` | Add an `emissions` record with `config_miem_file` |
| Dynamic output fields | `src/core_atmosphere/mpas_atm_core_interface.F` | Add `emis_<species>` diagnostics |
| MUSICA preflight | `scripts/check_build_env.sh` | Require the MIEM module and transitive libraries |
| Offline data preparation | New scripts under `scripts/` | Package and validate inventories on the exact MPAS grid |
| Test fixture | New files under `test_cases/chem_box/miem/` | Track canonical mesh/init/partition assets and generate a deterministic 64-cell inventory |
| User/developer documentation | `BUILD.md`, `RUN.md`, and `docs/chempas/` | Document dependency, preprocessing, coupling, and limitations |

## Target data flow

```text
source inventory
      |
      | external, scientifically selected remapping
      v
exact MPAS-cell fields
      |
      | prepare_miem_inventory.py: reorder, convert units, package, fingerprint
      v
global UPTEMPO inventory (cell j == MPAS global cell ID j)
      |
      | one full-grid MIEM instance on every rank
      v
MIEM surface_flux [kg m-2 s-1]
      |
      | indexToCellID(local owned cell) selects the global inventory slot
      v
rank-local species fluxes
      |
      | flux / (lowest-layer thickness * molar mass)
      v
MICM EMIS.<species> [mol m-3 s-1], level 1 only
      |
      v
normal MICM solve -> MICM-to-MPAS dry mass mixing ratios
```

## Required contracts

### Inventory and mesh contract

Every production inventory supplied to MIEM must satisfy all of the following:

1. `nCells` equals the number of cells in the global MPAS mesh.
2. The cell axis is global and one-based by convention: file slot `j` represents MPAS global cell ID `j`.
3. `indexToCellID` is a permutation of `1..nCells` in the source MPAS mesh used by preprocessing.
4. The packaged inventory records the geometry class, global IDs, geometry-appropriate cell coordinates, cell areas, identifying mesh attributes, and a deterministic mesh fingerprint.
5. Inventory species fields have shape `(Time, nCells)` and use `kg m-2 s-1` before MIEM species-map scaling.
6. `xtime` is Gregorian UTC and covers the complete model interval. MIEM does not wrap a climatology when time is outside the file range.
7. All values used by the model are finite and nonnegative.

The current MIEM API validates the cell count but does not expose inventory coordinates or cell IDs to CheMPAS-A. Therefore, exact mesh/order validation is a mandatory preprocessing and run-staging check. A file with the right count and wrong order would otherwise place valid fluxes on the wrong cells without an API error.

#### Canonical mesh fingerprint

Use one shared implementation in the preparation and validation tools. The first schema is named `chempas-mesh-sha256-v1` and has these normative rules:

1. Require `on_a_sphere` and normalize its trimmed value to `YES` or `NO`. Normalize `is_periodic` the same way when present. Record `is_periodic` and `sphere_radius` using the exact UTF-8 marker `<absent>` when either is missing.
2. Require common identity data: global `nCells`, `indexToCellID`, and `areaCell`. Require `latCell` and `lonCell` for a spherical mesh. Require `xCell`, `yCell`, and `zCell` for a planar mesh. Include any additional available cell-center coordinate variables from the fixed order `latCell`, `lonCell`, `xCell`, `yCell`, `zCell`.
3. Verify that `indexToCellID` is exactly a permutation of `1..nCells`, then reorder every cell array into ascending global-ID order before serialization.
4. Begin the byte stream with the exact ASCII bytes `chempas-mesh-sha256-v1\0`. Serialize fields in this fixed order: geometry class, `nCells`, `on_a_sphere`, `is_periodic`, `sphere_radius`, then `indexToCellID`, `areaCell`, and the present coordinate fields in the fixed order above. Encode each subsequent component as an unsigned big-endian 64-bit byte length followed by exactly that many bytes. For every numeric field, the components are its UTF-8 field name, trimmed UTF-8 units or `<absent>`, and normalized payload; this makes names, units, optional fields, and payload boundaries unambiguous.
5. Encode text as UTF-8, integer IDs as signed big-endian 64-bit values, and numeric attributes/arrays as IEEE-754 big-endian 64-bit values in C order. Reject nonfinite identity data and normalize negative zero to positive zero before hashing.
6. Store the SHA-256 digest plus the algorithm name and ordered field manifest in the inventory. Copy the normalized ancillary arrays into the inventory in ascending global-ID order.
7. Validate the exact digest as the acceptance gate. Also compare every identity array field-by-field with a documented tight tolerance so a failure reports the specific geometry, coordinate, area, or ordering difference rather than only a hash mismatch.

The shared helper must include a known-input/known-digest unit test. A planar mesh with identical all-zero `latCell`/`lonCell` values but permuted or changed `xCell`/`yCell` coordinates must fail validation.

### MPI contract

- `nCellsSolve` is the number of rank-owned cells and excludes halos from emissions application.
- `indexToCellID(1:nCellsSolve)` maps each local owned cell to a global inventory cell.
- Compute the global MIEM cell count from the global maximum of owned `indexToCellID`, using `mpas_dmpar_max_int` during initialization.
- Require every owned ID to lie in `1..global_nCells` and reject duplicate owned IDs on a rank.
- Construct `emissions_t(mechanism, global_nCells, 1, error)` on every rank.
- After each successful `run`, copy only the fluxes for owned global IDs into a rank-local array.
- Do not perform an MPI collective inside the per-step MIEM or chemistry error path. Existing rank-local early returns make downstream collectives unsafe.
- Accumulate any mass-budget statistics locally and reduce them only in `chemistry_finalize`.

### Species contract

For every species returned by `emissions%species_ordering`:

- the MICM species ordering must contain the same case-sensitive species name;
- the MICM rate-parameter ordering must contain `EMIS.<species>`;
- the MICM species must have a finite, positive molar mass;
- the species must be writable to an MPAS chemistry tracer; and
- host-bound, read-only species such as the current H2O binding are rejected as emissions targets.

At initialization, require a one-to-one match between the MIEM output species and the MICM `EMIS.*` parameters selected for coupling. Reject missing, duplicate, or extra configured emission parameters rather than partially enabling a source.

Use `%index(name)` for both MIEM and MICM buffer access. Do not assume that mapping iteration order equals storage order.

### Units and vertical placement

For species `s`, local owned cell `i`, and its global ID `g`:

```text
F(s,g)  = MIEM surface flux                         [kg m-2 s-1]
dz(i)   = zgrid(2,i) - zgrid(1,i)                  [m]
M(s)    = MICM molecular mass                       [kg mol-1]
R(s,i)  = F(s,g) / (dz(i) * M(s))                  [mol m-3 s-1]
```

Set `EMIS.<species>` to `R(s,i)` for MICM level 1 and to zero for every higher level. Dry-air density does **not** enter this conversion: MICM consumes a concentration tendency, and the existing MICM-to-MPAS conversion later applies `rho_dry` when it reconstructs dry mass mixing ratios.

The source mass identity used for validation is:

```text
R(s,i) * M(s) * dz(i) * areaCell(i) * dt
    = F(s,g) * areaCell(i) * dt                     [kg]
```

Reject nonpositive or nonfinite `dz`, nonpositive or nonfinite molar mass, and negative or nonfinite flux before modifying MICM rate parameters.

### Time contract

MIEM expects Unix epoch seconds for a Gregorian UTC timestamp. At a chemistry call:

```text
time_step     = accumulated chemistry dt, or dt when chemistry runs every step
interval_start = currTime - (time_step - dt)
epoch_seconds  = seconds(interval_start - 1970-01-01_00:00:00)
```

Pass `time_step` as `dt_seconds` to MIEM. With chemistry every step, `interval_start == currTime`. With `config_chemistry_interval > 0`, this selects the start of the accumulated chemistry interval rather than its final MPAS step.

Implement the conversion with MPAS timekeeping types and `mpas_set_time`, time/time-interval subtraction, and `mpas_get_timeInterval(..., dt=...)`; do not implement a separate civil-calendar algorithm. Reject `gregorian_noleap` and any other calendar when `config_miem_file` is nonempty.

MIEM currently returns an instantaneous/interpolated surface flux and may not use `dt_seconds`, but CheMPAS-A must pass the correct accumulated duration to preserve the API contract and future averaging behavior.

### Timestep ordering

The successful chemistry path becomes:

1. Apply chemistry cadence and determine `time_step`.
2. Derive the chemistry environment, including `zgrid`.
3. Update photolysis rates on their existing cadence.
4. Run MIEM once and select rank-owned surface fluxes.
5. Convert the fluxes and update `EMIS.*` in both MICM states.
6. Apply the existing lightning-NOx tracer injection, if configured.
7. Copy MPAS tracers and environment into MICM.
8. Solve MICM for all configured chemistry substeps with fixed photolysis and emissions rates.
9. Solve the optional reference state with the same rates.
10. Copy the coupled MICM state back to MPAS.
11. Commit MIEM diagnostics and local mass-budget accumulators only after the chemistry step succeeds.

### Failure and rollback contract

- Empty `config_miem_file`: no MIEM object, no inventory I/O, no emissions timer, and no change to current results.
- Initialization errors: log a chemistry-specific message and terminate through the existing critical-error path.
- MIEM file-read, time-coverage, count, or flux-validation errors during a step: terminate immediately. Retrying the same deterministic input is not useful.
- MICM solve failures after a successful MIEM update: use the existing chemistry tracer rollback. Do not publish the new flux diagnostics or add the step to the mass accumulator.
- Ensure every return path stops any timer it started and releases temporary arrays.
- The internal MIEM surface buffer is valid only after a successful `emissions%run`. The Fortran wrapper refreshes its pointer after every run because the underlying buffer may be reallocated; never cache that pointer independently in CheMPAS-A.

### Restart contract

MIEM is driven by absolute model time and needs no new restart field in Phase 1. A cold run and a split/restart run with `config_chemistry_interval=0` must select the same inventory times and produce equivalent results.

Nonzero `config_chemistry_interval` already keeps cadence accumulators only in module state. Exact restart equivalence for a restart that cuts through that interval is a pre-existing chemistry-cadence issue and is not added to the MIEM Phase 1 scope. Document and test MIEM restart equivalence at the default every-step cadence.

## Phase 0: Pin and verify the MUSICA dependency

The 2026-08-05 preflight found `musica_emissions.mod` and `libmiem` in the installed MUSICA prefix, and report/export modes passed. That result is not yet a sufficient static-link contract. The installed `musica-fortran.pc` reports `0.16.5` and includes `-lmiem`, but an emissions reference still has unresolved `nc_*` symbols unless NetCDF-C follows `-lmiem`. The committed MUSICA pkg-config template omits both MIEM and its NetCDF closure, while the installed file is a locally postprocessed artifact. The inspected build also has `MUSICA_USE_FMT=OFF`, so `fmt` is conditional rather than universally required. CheMPAS-A must not depend on a version-only pin or an uncommitted/generated dependency fix.

### Tasks

- [x] Select and record an exact MUSICA commit, its MIEM dependency commit, and any other dependency revisions that affect the exported static-link interface. Do not use `0.16.5` alone as the pin.
- [x] Land the MUSICA pkg-config-template correction upstream or select a pinned MUSICA revision that already contains the complete correction.
- [x] Ensure the generated `musica-fortran.pc` propagates `libmiem` and places NetCDF-C after it. Propagate NetCDF-Fortran only when the actual MUSICA/TUV-x archive closure requires it.
- [x] Make `fmt` part of the exported closure only when MUSICA was built with `MUSICA_USE_FMT=ON`.
- [x] Let the dependency build generate the platform C++ runtime (`-lstdc++` on the current Linux toolchain or `-lc++` on the supported LLVM/macOS toolchain); do not hard-code one runtime in CheMPAS-A's fallback data.
- [x] Confirm MUSICA Fortran was built with the same Fortran compiler as CheMPAS-A.
- [x] Confirm the installation contains `musica_micm.mod`, `musica_emissions.mod`, `libmusica-fortran`, `libmusica`, `libmiem`, `libmechanism_configuration`, `yaml-cpp`, NetCDF-C, and every build-enabled optional library.
- [x] Confirm `pkg-config --modversion musica-fortran` reports the expected API version and separately confirm the installed artifacts came from the pinned commit.
- [x] Confirm `pkg-config --libs musica-fortran` provides a complete, platform-correct static closure. At minimum, the MIEM portion must preserve this dependency order:

  ```text
  ... -lmiem ... -lnetcdf ... <build-selected C++ runtime>
  ```

- [x] Update `scripts/check_build_env.sh` so its module checks require both `musica_micm.mod` and `musica_emissions.mod`.
- [x] Update the preflight's generated fallback `.pc` data from the same dependency metadata so it includes MIEM, NetCDF-C, and only enabled optional libraries in linkable order.
- [x] Extend the preflight link probe to import both `musica_micm` and `musica_emissions` and actually construct/reference an emissions object so the static linker must pull `libmiem`; compile and link it using only `pkg-config --cflags --libs musica-fortran`.
- [x] Export the detected make target as `CHEMPAS_MAKE_TARGET` so documented build gates do not hard-code `llvm` on a gfortran environment.
- [x] Update `BUILD.md` from the older MUSICA 0.14.5 guidance to the exact MIEM-capable revision, dependency commits, build options, and verified transitive-library behavior.

### Disabled-path baseline capture

- [x] After installing the pinned dependency and before changing CheMPAS-A implementation code, build planning baseline `4eb4e677` in a separate clean worktree with the exact compiler, dependency prefix, precision, and build flags intended for the post-change comparison.
- [x] Run the existing ABBA, Chapman, and lightning-NOx cases with 8 MPI ranks and capture per-scientific-field NetCDF hashes, dimensions, configurations, logs, and exit status. Keep large output files as named external/CI artifacts rather than committing run data.
- [x] Track `test_cases/miem_disabled_baselines.json` as the machine-readable manifest containing the CheMPAS-A and dependency commits, compiler identity, build/run commands, configuration hashes, artifact location, and scientific-field hashes.
- [x] Define the post-change disabled comparison now: `config_miem_file=''`, the same pinned dependency/toolchain/configuration, bitwise-identical scientific fields, no inventory open, and no emissions diagnostic fields. Expected Registry/namelist schema additions are not scientific-field differences.
- [x] Refuse to claim E0 from outputs produced with a different MUSICA commit, compiler, precision, case input, or comparison policy.

### Gate

- [x] `scripts/check_build_env.sh` passes in report and export modes.
- [x] The emissions-constructing Fortran link probe links using only `pkg-config --cflags --libs musica-fortran`; removing the exported NetCDF-C closure causes the probe to fail as expected.
- [x] No CheMPAS-A build relies on an untracked or uncommitted MUSICA checkout change.
- [x] The pinned disabled-path baseline manifest and all referenced baseline artifacts exist and were captured before any Phase 1 or later implementation change.
- [x] Every Phase 0 stage or milestone was verified, committed, and pushed when completed.
- [x] After the Phase 0 gate passes, create or designate the verified Phase 0 checkpoint commit, push `develop_emissions`, and record and verify the remote SHA before Phase 1.

**Required phase checkpoint commit:** `build: require MIEM-capable MUSICA Fortran API`

## Phase 1: Establish the preprocessing and inventory contract

Spatial remapping is scientifically consequential and inventory-specific. CheMPAS-A will not select a universal interpolation algorithm. A production workflow first remaps the source inventory with an appropriate conservative tool, then the repository tooling validates, reorders, converts, and packages those already-remapped fields for MIEM.

### Files

- New `scripts/prepare_miem_inventory.py`
- New `scripts/validate_miem_inventory.py`
- New shared `scripts/miem_mesh_identity.py`
- New `miem_configs/README.md`
- New `miem_configs/chem_box_nox.yaml`
- New `test_cases/chem_box/miem/generate_fixture.py`
- New `test_cases/chem_box/miem/regenerate_assets.sh`
- New repository-controlled assets under `test_cases/chem_box/miem/assets/`: `chem_box_grid.nc`, `chem_box_init.nc`, and `chem_box.graph.info.part.8`
- New `test_cases/chem_box/miem/assets/manifest.sha256` and `test_cases/chem_box/miem/assets/PROVENANCE.md`
- New `test_cases/chem_box/miem/README.md`

### `prepare_miem_inventory.py` requirements

- [x] Accept an MPAS mesh/init file, an already-remapped source dataset, a source-variable mapping, source units, and an output path.
- [x] Read global `nCells`, `indexToCellID`, `areaCell`, `on_a_sphere`, optional geometry attributes, and every geometry-required coordinate from the authoritative MPAS file.
- [x] Require `latCell`/`lonCell` for spherical meshes and `xCell`/`yCell`/`zCell` for planar meshes. Never infer planar identity from all-zero latitude/longitude arrays.
- [x] Require the input data to identify the corresponding MPAS global cells; reject positional data with no verifiable cell identity.
- [x] Reorder every time/species field into ascending global cell-ID order.
- [x] Convert supported source units explicitly to `kg m-2 s-1`; reject unknown or ambiguous units.
- [x] Reject missing global IDs, duplicate IDs, NaN/Inf values, and negative values unless a future signed-flux mode is explicitly designed.
- [x] Write an UPTEMPO-compatible NetCDF file with dimensions `Time`, `nCells`, and `StrLen`; `xtime(Time,StrLen)`; and each inventory species as `(Time,nCells)`.
- [x] Preserve the requested time precision and write `xtime:calendar = "gregorian"`.
- [x] Include normalized ancillary `indexToCellID`, `areaCell`, geometry-required coordinates, all additional fingerprinted coordinates, and geometry attributes for external validation, even though MIEM currently ignores them.
- [x] Write provenance attributes for source file, source variable, source units, conversion, remapping tool/method supplied by the caller, creation command, and creation time.
- [x] Write the `chempas-mesh-sha256-v1` digest, algorithm identifier, and ordered field manifest through the shared mesh-identity helper.
- [x] Write atomically to a temporary file and rename only after all validation succeeds.
- [x] Never overwrite an existing output unless the caller explicitly supplies `--force`.

### `validate_miem_inventory.py` requirements

- [x] Compare the inventory against the exact MPAS mesh/init file that will be used for the run.
- [x] Require equal geometry class, identifying attributes, `nCells`, the full `1..nCells` global-ID sequence, matching area/geometry-appropriate coordinates within the diagnostic tolerance, and an identical exact mesh fingerprint.
- [x] Report field-specific identity failures, including planar `xCell`/`yCell`/`zCell` differences, rather than reporting only a digest mismatch.
- [x] Validate time monotonicity, Gregorian calendar metadata, requested run-time coverage, field shape, units, finiteness, and nonnegativity.
- [x] Accept `--start-time` and `--stop-time` so run staging fails before MPI launch when the inventory cannot bracket the simulation.
- [x] Print a concise success summary containing mesh fingerprint, cell count, time range, and species.
- [x] Return nonzero for any mismatch so scripts and CI can use it as a hard gate.

### Deterministic chem-box fixture

- [x] Track the compact canonical 64-cell mesh, initialized state, and 8-rank graph partition in the repository so the test does not depend on undeclared files under a developer's data directory.
- [x] Record SHA-256 hashes, generation commands, source commit/input, redistribution provenance, and exact versions of `planar_hex`, `MpasMeshConverter.x`, and `gpmetis` in the asset manifest.
- [x] Provide a deterministic regeneration script backed by a pinned environment or container. The active developer environment currently lacks those three generators, so ambient `PATH` is not an acceptable recipe.
- [x] Verify regenerated assets against the manifest. A user must be able to stage and run the checked-in assets without installing the generation toolchain.
- [x] Generate a 64-cell UPTEMPO fixture from the tracked canonical chem-box mesh rather than tracking a large production inventory.
- [x] Use the fixed times `2026-06-22_12:00:00`, `2026-06-23_00:00:00`, and `2026-06-23_12:00:00`, matching the tracked chem-box start and bracketing its 24-hour run. The interpolation test also samples `2026-06-22_18:00:00`, the midpoint of the first interval.
- [x] For zero-based time index `k=0,1,2` and global cell ID `g=1..64`, define the cell/time-signature inventory exactly as `nox_anth_sum(k,g) = 1.0e-12 * g * (k+1)` in `kg m-2 s-1`. The expected first-interval midpoint is `1.5e-12 * g`.
- [x] Make `generate_fixture.py` expose deterministic `zero`, `constant`, and `cell-time-signature` patterns. The constant pattern is exactly `1.0e-12 kg m-2 s-1` in every cell and time; the zero pattern is identically zero.
- [x] Include only the synthetic `nox_anth_sum` inventory field and apply `0.9` NO / `0.1` NO2 weights in `miem_configs/chem_box_nox.yaml`.
- [x] Define those weights explicitly as a **mass-flux split**, so `emis_NO:emis_NO2` is 9:1 in `kg m-2 s-1`. Do not assert a 9:1 molar-rate ratio: after conversion, `R_NO/R_NO2 = 9 * M_NO2/M_NO`.
- [x] Make generation deterministic and record the expected content hash for every pattern.
- [x] Keep paths in the MIEM YAML valid from the MPAS run directory; document that MIEM file patterns are resolved from the process working directory.

### Gate

- [x] A correctly generated 64-cell fixture passes validation.
- [x] A file with the wrong `nCells` fails.
- [x] A same-size file with two cell IDs or coordinates permuted fails for both a spherical test mesh and the planar chem-box mesh; the planar case must still fail when `latCell`/`lonCell` are all zero.
- [x] A file that does not bracket the requested run interval fails.
- [x] Repeated fixture generation produces byte-identical output or an explicitly documented stable-content hash if NetCDF metadata prevents byte identity.
- [x] A clean checkout contains or can deterministically regenerate every mesh/init/partition asset named by the chem-box test, and all tracked asset hashes pass.
- [x] Every Phase 1 stage or milestone was verified, committed, and pushed when completed.
- [x] After the Phase 1 gate passes, create or designate the verified Phase 1 checkpoint commit, push `develop_emissions`, and record and verify the remote SHA before Phase 2.

**Required phase checkpoint commit:** `feat: add exact-grid MIEM inventory preparation`

## Phase 2: Add the MIEM adapter, configuration, and lifecycle

### Files

- New `src/core_atmosphere/chemistry/musica/mpas_miem.F`
- Update `src/core_atmosphere/chemistry/musica/Makefile`
- Update `src/core_atmosphere/chemistry/Makefile`
- Update `src/core_atmosphere/chemistry/mpas_atm_chemistry.F`
- Update `src/core_atmosphere/Registry.xml`

### Namelist

- [x] Add an `emissions` namelist record under `MPAS_USE_MUSICA`:

  ```fortran
  &emissions
      config_miem_file = ''
  /
  ```

- [x] Define the option as a path to a MUSICA mechanism-configuration file containing an `emissions` section.
- [x] State in the Registry description that an empty path disables MIEM and that the referenced inventory must already use the exact global MPAS cell order.
- [x] Do not add a redundant `config_miem_enabled` flag.
- [x] Do not add an update interval; MIEM follows the chemistry solve cadence.

### `mpas_miem` responsibilities

- [x] Own `type(mechanism_t), pointer` and `type(emissions_t), pointer` objects from `musica_emissions`.
- [x] Own the enabled flag, global cell count, species names, MIEM storage indices, strides, and local cumulative emitted mass.
- [x] Expose a small MPAS-facing interface, conceptually:

  ```text
  miem_init(config_path, global_nCells, error_code, error_message)
  miem_get_species(n_species, names)
  miem_run(epoch_seconds, dt_seconds, indexToCellID, nCellsSolve,
           local_flux, error_code, error_message)
  miem_commit_mass(local_flux, areaCell, dt_seconds)
  miem_finalize(dminfo)
  miem_is_enabled()
  ```

- [x] Treat an empty path as a successful no-op without constructing a MUSICA object.
- [x] Construct `mechanism_t(trim(config_path), error)` and then `emissions_t(mechanism, global_nCells, 1, error)`.
- [x] Read every species name from `species_ordering%name(i)`, then resolve its storage index with `%index(name,error)` and cache that result.
- [x] Copy from `surface_flux` using `cell_stride` and `species_stride` only after each successful `run`.
- [x] Use the global ID from `indexToCellID(iCell)` in the MIEM buffer offset; never use local `iCell` as the global inventory index.
- [x] Validate associated pointers and buffer bounds before copying.
- [x] Deallocate the emissions object before the mechanism object so Fortran finalizers release the C++ handles in dependency order.
- [x] Prefix errors and logs consistently with `[MIEM]`.

### Chemistry initialization

- [x] Read `config_miem_file` and `config_calendar_type` in `chemistry_init`.
- [x] Preserve the current one-block-per-MPI-task requirement.
- [x] Retrieve the mesh pool and its `indexToCellID` array.
- [x] Compute `global_nCells` as the MPI maximum of owned global IDs.
- [x] Validate owned IDs before constructing MIEM.
- [x] Initialize MICM first and then MIEM; perform the cross-component species/rate validation in Phase 3.
- [x] Reject non-Gregorian calendars only when MIEM is enabled.
- [x] Zero MIEM diagnostic fields before the initial history write once Phase 4 is present. This is a Phase 4 task, not a Phase 2 gate.

### Build integration

- [x] Add `mpas_miem.o` to the MUSICA subdirectory `OBJS` list.
- [x] Add explicit module-object dependencies needed for reliable `make -j8` ordering.
- [x] Ensure `mpas_atm_chemistry.o` is built only after both MUSICA adapter modules are available.
- [x] Archive `mpas_miem.o` into `libchem.a` with the existing MUSICA objects.
- [x] Confirm the non-MUSICA build remains unaffected by preprocessor guards.

### Gate

- [x] The atmosphere core builds cleanly with `MUSICA=true` under the configured compiler.
- [x] It also builds with MUSICA disabled.
- [x] Empty `config_miem_file` logs one concise disabled message and opens no inventory.
- [x] A valid chem-box MIEM configuration initializes on 8 ranks and logs the same global cell count and species list on every rank without per-cell logging.
- [x] A non-Gregorian calendar fails during initialization with a specific `[MIEM]` message.
- [x] Confirm the pinned MIEM constructor is lazy: inventory file/count validation occurs in the first `emissions%run`, not in `emissions_t(...)`. The executable wrong-count assertion is therefore a Phase 3 gate.
- [x] Every Phase 2 stage or milestone was verified, committed, and pushed when completed.
- [x] After the Phase 2 gate passes, create or designate the verified Phase 2 checkpoint commit, push `develop_emissions`, and record and verify the remote SHA before Phase 3.

**Required phase checkpoint commit:** `feat: add MIEM Fortran lifecycle adapter`

## Phase 3: Couple MIEM fluxes through MICM emission reactions

### Files

- Update `src/core_atmosphere/chemistry/musica/mpas_musica.F`
- Update `src/core_atmosphere/chemistry/mpas_atm_chemistry.F`
- New or updated MICM test mechanism under `micm_configs/`

### MICM bookkeeping

- [x] Add an emission-entry type containing MIEM/MICM species name, MICM species index, `EMIS.*` rate-parameter index, and molar mass.
- [x] Add `musica_cache_emission_indices(names, error_code, error_message)`.
- [x] For each name, resolve the MICM species with `state%species_ordering%index(name,error)`.
- [x] Resolve `EMIS.<name>` with `state%rate_parameters_ordering%index(...)`.
- [x] Obtain the molecular mass from the MICM mechanism using the same property path already used for chemistry tracer conversion.
- [x] Match the species against `chem_species` and reject host-bound/read-only targets.
- [x] Require the MIEM species set and cached `EMIS.*` set to match exactly.
- [x] Leave all `EMIS.*` parameters at zero when MIEM is disabled.

### Rate setter

- [x] Add a routine conceptually named `musica_set_emission_fluxes` accepting rank-local fluxes, `zgrid`, `nCellsSolve`, and `nVertLevels`.
- [x] Validate dimensions and all physical inputs before changing either MICM state.
- [x] Set each cached emission parameter to zero for every local MICM grid cell and level, preventing stale upper-level values.
- [x] Convert and set the level-1 rate with `flux / (dz * molar_mass)`.
- [x] Use MICM's `rate_parameters_strides%grid_cell` and `%variable` for buffer offsets.
- [x] Apply identical values to `state` and, when allocated, `state_ref`.
- [x] Do not inject directly into MPAS mixing ratios; the source must participate in the normal MICM integration.

### Chemistry-step integration

- [x] Add a helper that converts `currTime` and accumulated chemistry duration to Unix epoch seconds through MPAS timekeeping.
- [x] Start a `chem MIEM` timer immediately before the MIEM call and stop it on every success/error path.
- [x] Run MIEM after `chem_env_fill` and before MPAS-to-MICM transfer and the MICM solve.
- [x] Select local owned fluxes with `indexToCellID`.
- [x] Set MICM emission rates once for the whole accumulated chemistry interval.
- [x] Keep those rates unchanged across all `config_chem_substeps`.
- [x] Ensure the first reference-state synchronization and all later reference solves see the same emissions rates as the coupled state.
- [x] Leave the existing lightning-NOx injection in place and document the ordering and potential for double counting.
- [x] Hold the local flux array until the MICM-to-MPAS copy succeeds so Phase 4 can publish only successful-step diagnostics.

### Test mechanism

- [x] Add a small MICM configuration containing writable NO and NO2 species and `EMISSION` reactions driven by `EMIS.NO` and `EMIS.NO2`.
- [x] Keep unrelated chemistry out of the mass-budget test mechanism so source mass can be isolated exactly.
- [x] Add a separate coexistence configuration or smoke case when both offline MIEM NOx and lightning NOx are active.

### Gate

- [x] A wrong inventory cell count fails on the first MIEM run with a specific `[MIEM]` message before either MICM state is modified.
- [x] A zero flux produces no change.
- [x] A constant flux yields the analytically expected level-1 concentration tendency.
- [x] All levels above level 1 retain zero `EMIS.*` rates.
- [x] The NO:NO2 surface-flux ratio is 9:1 for the fixture mapping.
- [x] The source result is unchanged when the same chemistry interval is divided into multiple MICM substeps, within solver tolerance.
- [x] Coupled and reference states receive identical chemistry forcing before transport-induced differences.
- [x] Missing species, missing `EMIS.*`, invalid molar mass, negative/nonfinite flux, and invalid layer thickness each produce a precise failure.
- [x] Every Phase 3 stage or milestone was verified, committed, and pushed when completed.
- [x] After the Phase 3 gate passes, create or designate the verified Phase 3 checkpoint commit, push `develop_emissions`, and record and verify the remote SHA before Phase 4.

**Required phase checkpoint commit:** `feat: drive MICM emissions from MIEM surface fluxes`

## Phase 4: Add runtime diagnostics and mass accounting

### Dynamic field discovery

The runtime-variable callback executes before full chemistry initialization, when a correctly sized MIEM object is not yet available. Diagnostic names belong to the MICM mechanism: a valid MIEM configuration may contain an empty mechanism species/reaction section and therefore cannot discover `EMIS.*` names. Use `config_miem_file` only to decide whether diagnostics are enabled, query `EMIS.*` rate parameters from `config_micm_file`, and require the actual MIEM output species to match that discovered set during chemistry initialization.

- [x] Add a lightweight `musica_query_emission_species(micm_config_path, ...)` beside `musica_query_species`; its path argument is always the MICM chemistry configuration.
- [x] Construct a temporary one-cell MICM state, inspect `rate_parameters_ordering`, select names beginning with `EMIS.`, strip the prefix, and return the species names.
- [x] Add a wrapper `chemistry_query_emission_species` so the core interface does not import MUSICA directly.
- [x] In `atm_prepare_runtime_chemistry_vars`, read both `config_miem_file` and `config_micm_file` as well as the existing photolysis settings.
- [x] When `config_miem_file` is nonempty, require a nonempty `config_micm_file` and call `musica_query_emission_species(config_micm_file, ...)`. Never pass `config_miem_file` to this query.
- [x] When `config_miem_file` is empty, skip emission-name discovery and add no emissions diagnostics, regardless of which `EMIS.*` parameters the MICM file contains.
- [x] Cache `n_runtime_emission_species` and `runtime_emission_species` independently of photolysis diagnostics.
- [x] During full initialization, cross-match the queried MICM names exactly against `emissions%species_ordering`; reject missing, duplicate, or extra names before the first chemistry step.
- [x] Add a regression with deliberately distinct MICM and MIEM configuration files, including a MIEM file with no mechanism species list, so accidentally querying the MIEM path fails the test.

### Runtime diagnostic fields

- [x] Extend `atm_add_runtime_chemistry_vars` to add one 2-D diagnostic per species:

  ```text
  name:        emis_<species>
  dimensions:  nCells
  units:       kg m^{-2} s^{-1}
  time levels: 1
  description: MIEM surface flux applied to chemistry for <species>
  ```

- [x] Add each field to both `diag` and `allFields`, following the current photolysis pattern.
- [x] Restructure the diagnostic callback so zero photolysis fields do not cause an early return when emissions diagnostics exist.
- [x] Zero every emissions diagnostic at initialization before any initial output.
- [x] Fill owned cells after a successful chemistry step; do not write halo cells as owned data.
- [x] Keep the previous successful diagnostic value when a recoverable MICM step rolls back.
- [x] Ensure users can select the fields in mutable output streams.

### Integrated source accounting

- [x] After a successful chemistry step, accumulate locally for each species:

  ```text
  emitted_mass_local(s) += sum_owned(F(s,g) * areaCell(i) * time_step)
  ```

- [x] Do not add a failed/rolled-back step.
- [x] Reduce the species arrays once in `chemistry_finalize` using `mpas_dmpar_sum_real_array`.
- [x] Log one concise global total in kg per species from the I/O rank.
- [x] Do not add any per-step collective.

### Gate

- [x] `emis_NO` and `emis_NO2` appear with the correct dimensions, units, and global spatial pattern in chem-box output.
- [x] The diagnostic NO:NO2 ratio is 9:1 wherever the source is nonzero.
- [x] The final integrated mass log equals the area integral of the fixture flux over successful chemistry intervals.
- [x] A no-MIEM run adds no emissions fields and performs no MIEM work.
- [x] A MIEM run with photolysis disabled still creates and fills emissions diagnostics.
- [x] Distinct `config_micm_file` and `config_miem_file` inputs discover diagnostics from MICM and then pass the exact MIEM/MICM species cross-check.
- [x] Every Phase 4 stage or milestone was verified, committed, and pushed when completed.
- [x] After the Phase 4 gate passes, create or designate the verified Phase 4 checkpoint commit, push `develop_emissions`, and record and verify the remote SHA before Phase 5.

**Required phase checkpoint commit:** `feat: expose MIEM flux diagnostics and budgets`

## Phase 5: Integration and regression testing

### Files and scenario definitions

- New `scripts/check_miem_throughput.py`
- New `scripts/test_miem_runtime_failures.py` and `scripts/test_miem_failure_paths.sh` for the eight-rank and focused-contract E12 gates
- New `scripts/test_miem_disabled_baselines.py` and `scripts/test_miem_disabled_baselines.sh` for E0 artifact validation, eight-rank reruns, canonical field hashing, and bitwise scientific comparison
- New `test_cases/chem_box/miem/scenarios.yaml` containing all run durations, chemistry timesteps, output intervals, fixture patterns, namelist overrides, expected assertions, and tolerances
- New `test_cases/chem_box/miem/throughput-report.schema.json` defining the versioned checker-report contract
- New `test_cases/chem_box/miem/stream_list.atmosphere.throughput` containing the split flux diagnostics, chemistry tracers, `rho`, `zgrid`, `areaCell`, `indexToCellID`, and `xtime` needed by the checker

### Test harness

- [x] Add `scripts/test_miem_integration.sh` or extend the existing smoke harness with an isolated MIEM mode.
- [x] Make the harness select one named case or all cases from `scenarios.yaml`; command-line overrides must be recorded in the result and must not silently change an expected value.
- [x] Create a temporary run directory; do not mutate tracked test-case namelists or delete user data.
- [x] Verify the canonical asset manifest, then stage the tracked 64-cell mesh/init data, tracked 8-rank partition, MICM config, MIEM config, and generated inventory.
- [x] Run `validate_miem_inventory.py` before every MIEM integration test.
- [x] Use 8 MPI ranks for all full MPAS runs, as required by this repository's test protocol.
- [x] Exercise 1-rank versus 8-rank mapping equivalence in a focused MPI adapter test that does not invoke the MPAS dynamics solver with an unsupported partition.
- [x] Keep NetCDF histories, restart files, and rank logs in the temporary run directory or CI artifact storage; never stage generated run output.
- [x] Preserve the complete run directory and comparison report on failure. On success, retain the compact JSON report and remove or expire large artifacts according to the test environment's policy.
- [x] Audit every produced rank log for nonzero error summaries, MIEM inconsistencies, and repeated initialization/finalization/timer rows before deleting successful run artifacts.
- [x] Automate E12: use eight-rank MPAS launches for missing file, wrong cell count, out-of-range time, and invalid calendar, and the focused MICM contract for missing species, missing `EMIS.*`, invalid flux, and invalid `dz`.

### Required automated run scenarios

| ID | Scenario name | Configuration and purpose |
|---|---|---|
| R0 | `disabled` | Empty `config_miem_file`; reproduce the pinned disabled baseline, open no inventory, and create no emissions diagnostics |
| R1 | `zero_flux` | MIEM enabled with the deterministic zero inventory; create zero `emis_NO`/`emis_NO2` fields, zero source totals, and no chemistry-tracer change |
| R2 | `constant_flux` | One chemistry interval with the constant inventory and emissions-only MICM mechanism; isolate unit conversion and exact source/tracer mass conservation |
| R3 | `cell_time_signature` | Cell/time-signature inventory with exact-time and midpoint samples; verify global-ID mapping, 90:10 mass split, interpolation, and 8-rank output assembly |
| R4 | `substeps_restart` | Matched continuous, split/restart, and multiple-chemistry-substep variants; verify identical MIEM sampling and equivalent results at every-step chemistry cadence |
| R5 | `lightning_coexistence` | Normal chemistry with both MIEM and lightning NOx intentionally enabled; verify separate MIEM diagnostics and documented combined tracer response without treating tracer delta as an MIEM-only budget |

All six scenario definitions and their configuration templates are tracked. R0-R5 full MPAS executions use 8 ranks; only the focused mapping adapter comparison may additionally use 1 rank.

### End-to-end output-throughput contract

For every history time written by a positive-source scenario and every global cell `g`, `check_miem_throughput.py` reconstructs the MIEM sample time from the recorded model clock and chemistry interval, interpolates the input fixture, and requires:

```text
F_NO_expected(t,g)  = 0.9 * F_NOx_inventory(t,g)
F_NO2_expected(t,g) = 0.1 * F_NOx_inventory(t,g)

emis_NO(t,g)  == F_NO_expected(t,g)                 [kg m-2 s-1]
emis_NO2(t,g) == F_NO2_expected(t,g)                [kg m-2 s-1]
```

The diagnostic at an output time represents the flux from the last successful chemistry interval; the checker must not compare it to the output timestamp without applying that interval-start convention. The initial output remains zero because no chemistry interval has yet succeeded.

For each species `s`, reconstruct every successful chemistry interval from the run configuration and compute:

```text
M_source(s) = sum_intervals sum_global_cells(
                F_s(interval_start,g) * areaCell(g) * dt_interval)
```

Require `M_source(s)` to match the rank-zero `[MIEM]` finalize total. In R2, the emissions-only mechanism has no chemical sinks, interconversion, transport loss, or other sources, so also compute dry tracer mass from the initial and final histories:

```text
M_tracer(s,t) = sum_global_cells sum_levels(
                  q_s(t,k,g) * rho_dry(t,k,g)
                  * (zgrid(k+1,g) - zgrid(k,g)) * areaCell(g))

M_tracer(s,final) - M_tracer(s,initial) == M_source(s)
```

Use output `rho`, which is MPAS dry-air density, and the species' dry mass mixing ratio from `scalars`. This tracer-mass equality is not applied to R5 or a normal reactive mechanism because NO and NO2 can react and interconvert; those runs verify applied flux diagnostics and source accounting instead.

The checker must:

- [x] Read the inventory, authoritative mesh/init file, scenario manifest, MPAS histories, and rank-zero log without modifying them.
- [x] Map all comparisons by `indexToCellID`, never by local or file position alone.
- [x] Directly compare every written `emis_NO`/`emis_NO2` value, check the derived `flux / (dz * molar_mass)` rate in the focused unit test, integrate source mass, and perform the R2 tracer-mass closure.
- [x] Emit a versioned JSON report containing scenario ID, input/output hashes, mesh fingerprint, commits/toolchain, expected and observed extrema, maximum absolute/relative errors, source/log/tracer mass totals, tolerances, timers, and an overall pass/fail value.
- [x] Exit nonzero on any failed assertion or missing required field. A warning-only throughput result is not a gate.
- [x] Record inventory and history byte counts plus the `chem MIEM` timer as I/O-performance telemetry. Report per-rank and aggregate effective rates separately because Phase 1 intentionally performs replicated reads; performance is informative, not a correctness gate.

### Required test matrix

| ID | Test | Pass criterion |
|---|---|---|
| E0 | MIEM disabled | With the exact Phase 0 dependency/toolchain/configuration, ABBA, Chapman, and lightning-NOx scientific-field hashes match the pinned baseline manifest bitwise; no inventory is opened and no emissions field is added |
| E1 | Exact-grid validation | Correct fixture passes; wrong count plus same-size spherical and planar coordinate/ID permutations fail before launch, including a planar mesh with all-zero lat/lon |
| E2 | Species mapping | Single NOx inventory species produces MIEM NO and NO2 surface mass fluxes at exactly 9:1; the molar-rate ratio includes their different molar masses |
| E3 | MPI mapping | Flux encoded by global cell ID appears on the same global MPAS cells in focused 1-rank and 8-rank tests |
| E4 | Vertical placement | `EMIS.*` is nonzero only in level 1; all upper levels are zero |
| E5 | Unit conversion | MICM rate equals `flux / (dz * molar_mass)` for selected cells |
| E6 | Global mass budget | In R2's emissions-only mechanism, emitted tracer dry mass increase and the finalize total both equal `sum(flux * areaCell * dt)` within a stated double-precision tolerance |
| E7 | Time interpolation | Inventory endpoints and midpoint produce the expected constant/linear values |
| E8 | Chemistry substeps | Changing `config_chem_substeps` does not resample MIEM within the outer chemistry interval |
| E9 | Restart | Continuous and split/restart runs agree with every-step chemistry |
| E10 | Reference solve | Coupled and reference states receive identical emission rates |
| E11 | Source coexistence | MIEM and lightning NOx both operate when intentionally configured, with their separate contributions documented |
| E12 | Failure paths | Missing file, missing species, missing `EMIS.*`, wrong count, out-of-range time, invalid calendar, invalid flux, and invalid `dz` fail clearly |
| E13 | Diagnostics | At every written time/global cell, `emis_<species>` fields match the correctly time-aligned applied fluxes and the finalize totals match the every-interval area/time integral |
| E14 | Diagnostic discovery | With distinct MICM and MIEM files, `EMIS.*` names come from `config_micm_file` and exactly cross-match the initialized MIEM species |
| E15 | Enabled zero source | R1 creates enabled but identically zero diagnostics and budgets and leaves chemistry tracers unchanged |
| E16 | Output throughput | R0-R5 produce schema-valid JSON reports; R2 closes inventory-to-diagnostic-to-log-to-tracer mass and all other applicable scenario assertions pass |

### Tolerances

- [x] Use exact comparison for IDs, species names, dimensions, zero upper-level rates, and disabled-path output where possible.
- [x] Use a documented tight relative tolerance for floating-point flux/rate/mass comparisons; do not leave tolerance implicit in scripts.
- [x] Scale absolute tolerances to the known fixture flux and expected mass rather than using a large universal epsilon.
- [x] Record CheMPAS-A, MUSICA, and MIEM commits; compiler; rank count; timestep; configuration hashes; and canonical asset manifest hash in test output.
- [x] Store scenario-specific numerical tolerances in `scenarios.yaml` and repeat the resolved values in the JSON report; the checker contains no hidden looser defaults.

### Full build and smoke gate

- [x] Run the repository preflight.
- [x] Perform a clean atmosphere build with the repository-required parallelism:

  ```bash
  make clean CORE=atmosphere
  find . -name "*.mod" -delete
  find . -name "*.o" -delete

  eval "$(scripts/check_build_env.sh --export)"
  build_args=(
    CORE=atmosphere
    PIO="$PIO"
    NETCDF="$NETCDF"
    PNETCDF="$PNETCDF"
    PRECISION=double
    MUSICA=true
  )
  if [[ -n "${NETCDFF:-}" ]]; then
    build_args+=(NETCDFF="$NETCDFF")
  fi
  make -j8 "$CHEMPAS_MAKE_TARGET" "${build_args[@]}"
  ```

- [x] Run all R0-R5 full MPAS scenarios with `mpiexec -n 8`, plus the focused 1-rank/8-rank adapter mapping comparison.
- [x] Run `check_miem_throughput.py` for every scenario and require all JSON reports to pass schema validation and their applicable correctness assertions.
- [x] Confirm R0 also matches the pinned ABBA, Chapman, and lightning-NOx disabled-path baselines, not only the chem-box disabled run.
- [x] Inspect all rank logs for critical errors, MIEM inconsistencies, and unexpected repeated I/O messages.
- [x] Run `git diff --check` and verify no generated run data or dependency artifacts are staged.
- [x] Every Phase 5 stage or milestone was verified, committed, and pushed when completed.
- [x] After the Phase 5 gate passes, create or designate the verified Phase 5 checkpoint commit, push `develop_emissions`, and record and verify the remote SHA before Phase 6.

**Required phase checkpoint commit:** `test: validate MIEM coupling on the MPAS grid`

## Phase 6: Documentation and release readiness

### Files

- New `docs/chempas/musica/MIEM_INTEGRATION.md`
- Update `docs/chempas/musica/MUSICA_INTEGRATION.md`
- Update `docs/chempas/musica/MUSICA_API.md`
- Update `docs/chempas/architecture/ARCHITECTURE.md`
- Update `docs/chempas/architecture/COMPONENTS.md`
- Update `BUILD.md`
- Update `RUN.md`
- Update `test_cases/README.md`
- Regenerate or update the namelist reference derived from `Registry.xml`

### Required content

- [x] State prominently that Phase 1 inventories must be pregridded to the exact MPAS mesh and global cell order.
- [x] Document the inventory packaging and mandatory validation commands.
- [x] Document the UPTEMPO field/time/unit requirements and the complete `chempas-mesh-sha256-v1` schema, including distinct spherical and planar coordinate requirements.
- [x] Document the tracked chem-box assets, manifest verification, pinned regeneration environment, and staging workflow; repair the stale test-case generation references.
- [x] Explain the replicated full-grid-per-rank implementation and its memory/I/O cost.
- [x] Explain `config_miem_file`, relative-path behavior, and the empty-string disabled path.
- [x] Show separate MICM chemistry and MIEM emissions configuration examples, and state that diagnostic `EMIS.*` discovery reads `config_micm_file` while `config_miem_file` only enables MIEM.
- [x] Explain the `EMIS.<species>` naming contract and surface-flux conversion equation.
- [x] Explain why dry-air density is not part of the surface-flux-to-MICM-rate conversion.
- [x] Document the Gregorian-only and inventory-time-coverage requirements.
- [x] Document `emis_<species>` diagnostics and final integrated mass logs.
- [x] Document R0-R5, `scenarios.yaml`, the throughput-checker command, its JSON schema, the interval-start diagnostic convention, and the inventory-to-diagnostic-to-log-to-tracer accounting equations.
- [x] Explain that direct NO/NO2 tracer-mass closure is valid only for the emissions-only mechanism; reactive/coexistence runs validate applied source accounting because chemistry changes those species.
- [x] Describe the recorded I/O telemetry as non-gating Phase 1 information and explain replicated per-rank reads.
- [x] Explain coexistence and possible double counting with lightning NOx.
- [x] State the Phase 1 limitations and the planned distributed-I/O follow-up.
- [x] Record the tested MUSICA and MIEM commits, conditional build features, verified static-link closure, compiler, build command, and 8-rank test command.
- [x] Document the Phase 0 disabled-path baseline manifest and the exact conditions under which E0 may be compared.
- [x] Document the commit-and-push checkpoint cadence and where implementers record pushed SHAs and verification results.

### Gate

- [x] A new user can build, validate an inventory, stage the chem-box example, run it on 8 ranks, and identify the emissions diagnostics using only tracked documentation.
- [x] Documentation examples use the same filenames, namelist keys, units, and species names as the tested configurations.
- [x] No documentation implies that MIEM or CheMPAS-A performs runtime regridding in Phase 1.
- [x] Every Phase 6 stage or milestone was verified, committed, and pushed when completed.
- [x] After the Phase 6 gate passes, create or designate the verified Phase 6 checkpoint commit, push `develop_emissions`, and record and verify the final remote SHA.

**Required phase checkpoint commit:** `docs: document MIEM emissions workflow`

## Phase 7: Activated scalability work

This phase was originally deferred from the Phase 1 completion gate and was
activated on 2026-08-06 by the request to complete every phase. Its normative
API, ownership, validation, vertical-source, diagnostic, regridding-decision,
and benchmark contracts are in
`docs/chempas/musica/MIEM_SCALABILITY_DESIGN.md`.

- [x] Propose an upstream MUSICA/MIEM API that accepts selected global cell IDs or a host-to-inventory index map.
- [x] Add rank-local/hyperslab inventory reads so each rank does not construct a full global emissions state.
- [x] Expose inventory grid metadata through the API for in-model mesh/order validation.
- [x] Evaluate native regridding only after conservation, ownership, and parallel-I/O semantics are specified.
- [x] Add support for elevated or vertically distributed sources when MIEM exposes the required state and metadata.
- [x] Add sector/category diagnostics without multiplying memory unboundedly.
- [x] Benchmark initialization time, per-step time, and memory on regional and global production meshes before choosing the distributed design.

### Activated stages

- [x] Specify selected-cell ordering, reader ownership, mesh metadata, vertical-profile, bounded-diagnostic, native-regridding, and benchmark contracts.
- [x] Extend and verify MechanismConfiguration for normalized vertical profiles.
- [x] Extend and verify MIEM selected-cell readers, metadata, layer fluxes, and bounded diagnostics.
  - [x] Add validated ordered cell selections and coalesced NetCDF hyperslab reads, with full-grid/selected bitwise-equivalence tests.
  - [x] Expose selected inventory grid metadata and reject inconsistent source metadata.
  - [x] Produce mass-closing per-level fluxes for surface and normalized-profile sources.
  - [x] Allocate and populate only explicitly requested sector/category diagnostics within a configured cap.
- [x] Extend and verify MUSICA C/Fortran bindings for the Phase 7 MIEM API.
  - [x] Pin the verified MechanismConfiguration and MIEM scalability revisions.
  - [x] Extend the MUSICA C++ wrapper for selections, metadata, layered flux, and bounded diagnostics.
  - [x] Extend and verify the MUSICA C ABI for selections, metadata, layered flux, and bounded diagnostics.
  - [x] Extend and verify the Fortran API while retaining the full-grid constructor.
- [x] Pin the pushed dependency revisions and pass CheMPAS preflight/static-link probes.
- [x] Replace the replicated CheMPAS adapter with selected-cell construction and in-model metadata validation.
- [x] Register and publish bounded sector/category and optional layered diagnostics.
- [x] Add deterministic unit, negative, one-rank/eight-rank, and full MPAS regression coverage.
- [x] Run and record regional/global production-mesh benchmark reports.
- [x] Update build, run, API, architecture, test, limitation, and implementation-log documentation.

### Gate

- [x] Selected and replicated MIEM modes are bitwise equal for every requested global cell across all R0-R5 inventory times.
- [x] An 8-rank run reads and allocates only rank-owned inventory cells and validates selected geometry before MICM mutation.
- [x] Wrong geometry/order metadata fails in-model even if standalone validation was bypassed.
- [x] Surface and normalized multi-level profiles close source, diagnostic, log, and tracer-mass accounting.
- [x] Requested sector/category diagnostics close to totals and the configured field cap rejects unbounded allocation.
- [x] Regional and global benchmark reports prove selected-cell payload/state scaling and record initialization, warm-step, and peak-RSS measurements.
- [x] Clean dependency, MUSICA, CheMPAS MUSICA/non-MUSICA builds and all positive, negative, E0, and documentation gates pass.
- [x] No documentation or implementation enables native runtime regridding.

### Checkpoint

- [x] Apply the same local verification, focused commit, and push rule to every activated Phase 7 stage or milestone.
- [x] When the agreed Phase 7 scope is complete, create or designate its verified phase checkpoint commit, push `develop_emissions`, and record and verify the remote SHA.

**Required phase checkpoint commit:** `feat: complete distributed MIEM emissions scalability`

**Verified phase checkpoint:** `b8e7d3764faa5c89242d0a4c30ce9d65c5f549d2`; `origin/develop_emissions` resolved to the same SHA after push.

## Phase 8: Verified emissions visualization and extended throughput evidence

Phase 8 turns the existing numerical gates into a reproducible emissions
figure bundle without treating synthetic forcing as a scientific inventory.
Its checkpoint is subject to the same verify, focused-commit, push, and
remote-SHA discipline as every earlier phase and milestone.

### Plotting and provenance scope

- [x] Add `scripts/plot_miem_emissions.py` and focused unit tests.
- [x] Use the plotting protocol in `scripts/style.py`: NCAR colors, fonts, and
  chemical labels; explicit physical units; final reference frames for spatial
  and vertical diagnostics; all frames for budget histories; rasterized dense
  fills; and 300-dpi PNG plus vector PDF output.
- [x] Read horizontal coordinates from the authoritative MPAS mesh rather than
  assuming they are copied into `output.nc`, and require exact
  `indexToCellID` equality between mesh and history.
- [x] Fail closed on missing/nonfinite/negative diagnostics, wrong units,
  nonzero initial emissions, missing layered or group closure, a failed R2,
  R3, or R6 throughput assertion, or a history/report SHA-256 mismatch.
- [x] Write `chempas-miem-figure-manifest-v1` with hashes and byte sizes for
  every model input, report, PNG, and PDF; selected frames; run configuration;
  and independently calculated closure errors.
- [x] Keep synthetic inventories and NetCDF histories in temporary run roots;
  commit only the small figures and provenance manifest. Production plots
  require an external, science-grade inventory already conservatively remapped
  onto the exact production mesh.

### Evidence runs and longer-run decision

- [x] Clean-build the double-precision MUSICA-enabled executable against the
  pinned dependency stack before generating the evidence.
- [x] Run R3 `cell_time_signature/exact_start` on 8 MPI ranks for the
  nonuniform exact-grid NO/NO2 map and configured 9:1 split.
- [x] Run R6 `layered_diagnostics` on 8 MPI ranks for normalized 25%/75%
  elevated allocation and total/sector/category closure.
- [x] Extend emissions-only R2 `constant_flux` to 1,800 seconds with 60-second
  output on 8 MPI ranks. Use all 31 frames and all 600 chemistry intervals to
  demonstrate stable diagnostic-integral, model-reported end-of-run source,
  and dry-tracer mass closure.
- [x] Do not lengthen R3 or R6 solely for visualization: their deterministic
  spatial and diagnostic-allocation contracts are established by the first
  applied interval.
- [x] Defer longer science integration until a science-grade exact-grid
  inventory and transport/chemistry question are defined. At that point, use a
  one-hour production-grid throughput shakedown before a run covering at least
  one complete diurnal cycle; replace emissions-only tracer-equality checks
  with scientifically valid reactive/source budget expectations.

### Gate and checkpoint

- [x] Visually inspect all three PNGs for units, labels, color contrast,
  clipping, and legend/title overlap.
- [x] Pass focused plot/report tests, complete Python discovery, syntax checks,
  local-document links, canonical asset verification, and `git diff --check`.
- [x] Stage only Phase 8 script, tests, documentation, figures, manifest, plan,
  and implementation-log changes; preserve unrelated worktree content.
- [x] Commit `feat: add verified MIEM emissions plots`, push
  `develop_emissions`, and verify that `origin/develop_emissions` resolves to
  the exact local checkpoint SHA.

**Required phase checkpoint commit:** `feat: add verified MIEM emissions plots`

**Verified phase checkpoint:** `50086b0597f33ba6c84092885f57577f57427ea4`;
`origin/develop_emissions` resolved to the same SHA immediately after push.

## Phase 9: Global coupled emissions, dynamics, and chemistry

Phase 9 closes the remaining scale and realism gap. The existing x1.40962
benchmark proves selected-cell MIEM I/O on a 40,962-cell spherical mesh, but it
is a public-Fortran-API harness rather than an `atmosphere_model` integration.
The existing 24-hour global Chapman-NOx atmosphere case runs dynamics and
chemistry with `config_miem_file=''`. Neither result proves a global atmosphere
run with dynamics, reactive chemistry, and MIEM emissions active together.

Phase 9 is complete only after a versioned science-grade inventory is
conservatively remapped and packaged for the exact global mesh, a gated
shakedown ladder passes, and at least one full-diurnal global atmosphere run
produces reproducible source, chemistry, dynamics, restart, performance, and
provenance evidence.

### Fixed boundaries and scientific contract

- [x] Use the existing 40,962-cell, 26-level spherical x1.40962 mesh and its
  verified 8-rank partition for the first global integration ladder. A later
  production rank count requires a separately hashed partition and a
  rank-equivalence check before it can replace the 8-rank reference.
- [x] Use the existing idealized x1.40962 state only for software shakedowns.
  The science acceptance run requires date-matched meteorological initial and
  surface/forcing data on the same mesh; record their origin, processing,
  timestamp, license, and SHA-256 values.
  - A1 resolves the pinned NOAA GFS v16.3 2024-07-01 00Z atmosphere and
    surface analysis through WPS 4.6.0 into a 26-level, 45-km x1.40962 state.
    `stage9d-meteorology-audit.json` verifies provider ETags, every derived
    SHA-256, the exact mesh, finite/bounded atmosphere and surface fields, and
    bitwise preservation while the declared Chapman-NOx background is added.
- [x] Select or author a reactive MICM mechanism that contains every emitted
  species, a writable `EMIS.<species>` parameter for each one, compatible MPAS
  tracers, and the required TUV-x photolysis reactions. Pass the standalone
  MICM/MIEM contract test before any global model allocation.
- [x] Scope the first science inventory to explicit NO and NO2 mass fluxes.
  If the source product reports aggregate NOx—commonly on an NO2-equivalent or
  nitrogen-mass basis—record the original basis and the scientifically
  justified speciation and molecular-mass conversion. Never infer a 9:1 split
  from the synthetic test fixture.
- [x] Choose the inventory version and simulation period together so raw
  timestamps bracket the complete run, including restart boundaries and any
  spin-up. Require a Gregorian calendar until the implemented time contract is
  deliberately extended.
- [x] Keep raw inventories, remapping weights, packaged NetCDF, global initial
  conditions, partitions, and model histories outside Git under a dedicated
  `CHEMPAS_EMISSIONS_DATA_ROOT`. Commit only small configurations, schemas,
  reports, plots, and a manifest that resolves every external artifact by
  source identifier and SHA-256.
- [x] Preserve the no-runtime-regridding boundary. All horizontal remapping is
  an explicit preprocessing step; CheMPAS receives a validated exact-grid
  inventory in ascending global `indexToCellID` order.

### Stage 9A — acquire and qualify a science-grade inventory

- [x] Select a published, research-appropriate UPTEMPO- or ECCAD-compatible
  product with a stable version/DOI, provider URL, redistribution terms,
  temporal resolution, native grid description, species/sector definitions,
  uncertainty documentation, and complete coverage of the target period.
- [x] Download or receive the raw product outside the repository, verify any
  provider checksum, compute repository-standard SHA-256 values, and create a
  machine-readable acquisition manifest. Never silently replace a file under
  an existing version identifier.
- [x] Define treatment of missing values, ocean/land masks, point sources,
  negative corrections, units, time zones, leap/calendar behavior, and sector
  aggregation before remapping. Fail on unresolved or scientifically
  ambiguous metadata rather than substituting zero.
- [x] Record all transformations from native inventory variables to MIEM
  species, including NOx speciation, molecular weights, temporal profiles,
  vertical allocation, and any excluded sectors. Preserve source-sector
  fields needed for diagnostic closure.
- [x] Create an inventory audit report with global and regional totals per
  source time/species/sector in both native units and `kg m-2 s-1`.

**Stage 9A gate:** the inventory is scientifically identified, legally usable,
temporally suitable, checksummed, and chemically mapped without relying on a
synthetic-fixture convention.

**Required Stage 9A checkpoint:** `data: record global MIEM inventory provenance`

### Stage 9B — conservative exact-grid preprocessing

- [x] Generate and retain conservative remapping weights from the native
  inventory grid to x1.40962 with a named tool/version and explicit source and
  destination masks. Hash the weight file and all grid descriptors.
- [x] Audit native versus remapped integrated mass for every time, species,
  and retained sector. Record absolute/relative differences, unmapped area,
  mask handling, and the tolerance justified for this dataset; do not accept a
  remap merely because it completed.
- [x] Package the already-remapped fields with
  `scripts/prepare_miem_inventory.py`, including remapping provenance and the
  authoritative `chempas-mesh-sha256-v1` identity.
- [x] Run `scripts/validate_miem_inventory.py` against the exact model init
  file and complete intended time window. Reject wrong cell order, geometry,
  units, missing/nonfinite/negative data, incomplete coverage, and fingerprint
  mismatch.
- [x] Run the selected-cell MIEM harness on all inventory endpoints and
  representative midpoints before launching MPAS. Prove 8-rank ownership
  covers the global grid once and selected/full flux streams are bitwise equal.
- [x] Plot remapped source totals, spatial distributions, time evolution,
  sector sums, and any vertical profiles; obtain a scientific review of the
  audit before model use.

**Stage 9B gate:** exact-grid packaging passes structural validation, the
conservative-remap budget passes its declared tolerance, all selected-cell
samples match, and the inventory audit is reviewed.

**Required Stage 9B checkpoint:** `feat: add science-grade global MIEM inventory workflow`

### Stage 9C — full-atmosphere shakedown ladder

Every model rung uses `atmosphere_model` with dynamics, tracer transport,
reactive MICM chemistry, TUV-x, and 8 MPI ranks. Each rung must pass before the
next begins. A failure creates the smallest targeted reproducer and a pushed
fix checkpoint before the failed rung is retried; longer runs are not used to
debug an unresolved shorter-run failure.

| ID | Duration/input | Required evidence |
|---|---|---|
| G0 | 5 min, MIEM disabled versus enabled zero flux | Bitwise-equal meteorology and chemistry fields; no source mass; enabled path opens and validates the global inventory |
| G1 | 15 min, bounded synthetic constant/cell-signature inventory | Exact global-ID placement, finite diagnostics, configured species split, and diagnostic-to-logged-source closure |
| G2 | 1 h, synthetic time-varying inventory | All output-frame interpolation checks, stable memory/timers, and continuous versus 30+30 min restart equivalence |
| G3 | 1 h, science-grade inventory | Exact sampled fluxes, source/sector/layer closure, finite physical state, output-size and wall-time forecast |
| G4 | 6 h, science-grade inventory | Multiple photolysis/emissions cycles, restart checkpoint, no accumulating source-budget drift, acceptable resource use |

- [x] Add tracked global scenario definitions and an isolated staging driver;
  never adapt the 64-cell chem-box harness by silently weakening its contracts.
- [x] Extend the throughput checker/report schema for multiple output files,
  global restart segments, externally manifested inputs, inventory sectors,
  reactive chemistry budgets, and non-chemistry field comparisons.
- [x] Preflight disk, memory, wall-clock allocation, output cadence, restart
  cadence, and cleanup policy before G3/G4. Keep complete histories external;
  retain compact reports and scientific-field hashes in Git.
- [x] Keep lightning and other NOx sources disabled through G3 so the first
  coupled source budget isolates MIEM. Add a later coexistence rung only with
  separate source diagnostics and an inventory known not to double-count the
  enabled online source.

**Stage 9C gate:** G0-G4 pass on the same executable/dependency stack intended
for the acceptance run, with schema-valid reports and no unexplained dynamics,
chemistry, restart, source, or resource regression.

**Required Stage 9C checkpoint:** `test: add global coupled MIEM shakedowns`

### Stage 9D — full-diurnal science acceptance run

**A0 promotion evidence:** the date-matched one-hour acceptance-stack shakedown
passes in `stage9d-a0-report.json` from clean CheMPAS commit `5c3daa17` and the
same `ff7166f1...` atmosphere executable used by G0-G4. All 16 report
assertions pass, including exact-grid/open lifecycle, every-frame inventory
interpolation, diagnostic and logged-source closure, interval/cumulative NOy
closure, finite dynamics and chemistry, and the resource guard. The retained
external run used 8 MPI ranks, completed 8 model/MIEM steps in 71.97 wall
seconds, and peaked at 887,928 KiB RSS. This promotion shakedown does not
replace the required 24-hour A1 trajectory, restart, or matched control.

**A1 restart-audit correction:** the first retained A1 evaluation completed all
four trajectories and passed every non-restart gate, but exposed a checker
error: it compared the largest absolute error and largest relative error from
different cells rather than applying the declared combined bound to each
element. The corrected checker records maximum normalized elementwise error,
keeps chemistry at `5e-11` relative plus `1e-20 kg kg-1` absolute, and gives
recomputed TUV-x photolysis its own `2e-10` relative plus `1e-20 s-1` absolute
bound. The observed worst photolysis relative difference is `1.313e-10`; all
meteorology, dynamics, and emissions fields remain bitwise-gated. The complete
retained run is re-evaluated after the focused fix checkpoint is pushed.

**A1 trajectory evidence:** `stage9d-a1-report.json` passes all 47 closed
assertions for the retained 24-hour continuous, 12+12-hour restart, and matched
no-MIEM trajectories. Every non-chemistry restart field is bitwise identical;
the largest normalized chemistry/photolysis restart error is 0.8165 under its
declared elementwise bound. The emitted trajectory and control preserve NOy to
maximum hourly relative residuals of `4.604e-12` and `1.571e-13`, respectively,
while the emitted-minus-control response closes at `1.435e-11`. All four
geographic photolysis anchors observe day and night. The continuous run
advances 47.58 simulated seconds per wall second, spends 765.41 seconds in
chemistry and 8.66 seconds in MIEM, and peaks at 1,044,480 KiB RSS. Partition
accounting records 5,102-5,140 selected cells and 2,408,144-2,426,080 modeled
first-open payload bytes per rank; total histories and restarts occupy
16,162,160,820 bytes. The 12-hour restart stream read costs 1.562 seconds.

**A1 visualization evidence:** `plot_global_miem_science.py` fails closed on a
nonpassing report, external-manifest mismatch, packaged-inventory mismatch,
selected-history hash/size mismatch, wrong time/grid/order/units, or invalid
science fields. Its three inspected 300-dpi PNG/vector-PDF pairs show global
NO/NO2 source and matched-control response, source-to-NOy closure and retained
sectors, and complete photolysis/vertical/hemispheric behavior. The portable
`stage9d-figure-manifest.json` pins the 47-assertion A1 report, exact external
manifest and inventory, final enabled/control histories, plotting code/style,
software commits, executable, selections, validations, and every figure hash.

- [x] Run at least 24 continuous simulated hours with date-matched dynamics,
  science-grade inventory, reactive MICM chemistry, TUV-x, MIEM, and a bounded
  diagnostic set. If concentration interpretation requires chemical spin-up,
  extend the run or initialize from a spun-up state and record the scientific
  rationale; do not label the first-day concentrations production-ready by
  default.
- [x] Run a restart-equivalent trajectory covering the same period and compare
  the continuous/restarted scientific fields at every common output time under
  declared exact or numerical tolerances.
- [x] Run the matched no-MIEM or zero-source control needed to isolate the
  emissions response. Require meteorological fields to follow the expected
  deterministic relationship and explain any non-chemistry divergence.
- [x] At every output and globally integrated interval, reconstruct applied
  `emis_<species>` from the packaged inventory and require diagnostic and
  model-reported emitted mass to close to `sum(flux * areaCell * dt)`.
- [x] Do not require emitted NO and NO2 masses to equal their individual tracer
  changes in a reactive run. Instead, define a mechanism-aware elemental-N or
  NOy budget, including deposition, boundary exchange, lightning, and other
  sources when enabled. If the required tendency terms are unavailable, add
  those diagnostics before making a chemistry mass-closure claim.
- [x] Check all chemistry tracers and emission diagnostics for missing,
  nonfinite, or disallowed negative values; audit global/hemispheric/sector
  totals, vertical distributions, NO/NO2/NOy evolution, and diurnal behavior.
- [x] Record MIEM first-open/warm-step timers, total chemistry cost, peak RSS,
  per-rank selected cells and payload, output volume, restart cost, and model
  throughput. Performance is reported against the G0 control but is not traded
  against scientific correctness.
- [x] Generate protocol-compliant PNG/PDF figures and a SHA-256 manifest tied
  to the passing global throughput report and exact external-input manifest.

**Stage 9D gate:** the full-diurnal run and restart/control comparisons pass;
source accounting closes; reactive chemistry has a scientifically valid
budget; dynamics and chemistry remain stable; and all evidence is reproducible
from versioned manifests and commands.

**Required Stage 9D checkpoint:** `test: validate global MIEM diurnal science run`

### Stage 9E — reproducibility and release evidence

**Release evidence:** `stage9e-release-manifest.json` closes every named gate
against evidence-base commit `4ffc5da9...` and executable
`ff7166f1...`. The empty-root G3 rerun passes 20 assertions. The retained A1
recheck passes all 47 assertions and is canonically identical to the accepted
Stage 9D report after excluding only volatile free-disk telemetry. Its three
inspected PNG/PDF pairs remain pinned by the portable figure manifest.

**Regression evidence:** all nine R0-R6 reports pass, as do selected/full and
one/eight-rank mapping and the six expected runtime failure paths. Strict E0
passes for ABBA, Chapman-NOx, and lightning-NOx against pre-emissions CheMPAS-A
source rebuilt with the candidate dependency stack. The original Phase 0
manifest remains archived, and all 195 canonical scientific field hashes are
identical between historical and same-stack captures.

**Evidence boundary:** compact reports, logs, field manifests, commands,
dependency/compiler/partition/inventory identities, and SHA-256 records are
tracked. Inventories, meteorology, histories, restarts, run trees, and baseline
NetCDF outputs remain immutable external artifacts under
`CHEMPAS_EMISSIONS_DATA_ROOT` with the retention policy recorded in the release
manifest. This validates coupled software/process behavior; it does not turn
the idealized, unspun first-day Chapman-NOx concentrations into production
air-quality estimates.

- [x] Recreate staging from an empty work directory using only tracked code,
  configuration, and external manifest-resolved inputs; rerun at least G3 plus
  the decisive acceptance comparisons.
- [x] Track versioned JSON reports, field-hash manifests, run commands,
  dependency/compiler/partition identities, inventory provenance, conservation
  audit, resource measurements, and plot manifest. Keep large raw/remapped/run
  data external and state its retention location and policy.
- [x] Update build, run, emissions, visualization, architecture, limitation,
  and implementation-log documentation. State explicitly which conclusions
  are software validation versus scientific interpretation.
- [x] Run the complete R0-R6/E0 regression suite after the global work and
  confirm the new Phase 9 paths do not weaken the existing disabled, chem-box,
  mapping, vertical, diagnostic, or failure contracts.
- [x] Commit and push each Stage 9A-9E milestone independently, verify the
  remote SHA before advancing, then record the final Phase 9 checkpoint.

**Required Stage 9E and Phase 9 checkpoint:**
`feat: complete global coupled MIEM validation`

**Verified Stage 9E and Phase 9 checkpoint:**
`2b172b03f16337b5c84f6812c16c9cd8e04649fe`; immediately after push,
`origin/develop_emissions` resolved to the same SHA. The following audit-only
documentation checkpoint records that already-verified result.

### Planned tracked artifacts

- `EMISSIONS.md` — concise CheMPAS-A emissions architecture and code map.
- `test_cases/global_miem/scenarios.yaml` — G0-G4 and acceptance definitions.
- `test_cases/global_miem/external-inputs.schema.json` and a versioned input
  manifest containing source identifiers, licenses, paths, sizes, and hashes.
- `scripts/run_global_miem_integration.sh` — isolated staging and promotion
  ladder driver.
- `scripts/check_global_miem_throughput.py` and a versioned global report
  schema.
- `docs/chempas/musica/global-runs/` — compact audit, throughput, restart,
  performance, and figure manifests.

## Implementation invariants

These invariants should remain visible in code comments and tests:

- `config_miem_file == ''` means no MIEM construction or I/O.
- `config_miem_file` gates emissions diagnostics; `config_micm_file` is the sole source for runtime `EMIS.*` diagnostic-name discovery.
- MIEM cell indices are global; MICM/MPAS chemistry cells are rank-local and vertically flattened.
- Only `indexToCellID` connects those two index spaces.
- MIEM is constructed with global `nCells`, the actual MPAS vertical-level count, and an ordered selection containing only rank-owned global cell IDs.
- Inventory slot `j` means MPAS global cell ID `j`.
- Mesh identity is geometry-aware: spherical identity requires latitude/longitude, while planar identity requires Cartesian cell centers; cell count and all-zero planar latitude/longitude are insufficient.
- `chempas-mesh-sha256-v1` is computed by one shared canonical implementation over normalized global-ID order.
- MIEM output is a surface mass flux, not a mixing-ratio tendency.
- `EMIS.*` is a molar concentration tendency.
- The lowest-layer thickness is `zgrid(2,i)-zgrid(1,i)`.
- Emission rates are set once per chemistry solve and frozen across MICM substeps.
- MIEM and photolysis update independently but both are set before MICM solves.
- The coupled and reference MICM states use identical emissions rates.
- Diagnostics and mass totals represent successful chemistry steps only.
- An emissions diagnostic written after a successful solve represents the flux applied for that chemistry interval, sampled at its interval start; initial diagnostics are zero.
- Direct emitted-mass versus NO/NO2 tracer-mass equality is asserted only in the emissions-only mechanism, not in a reactive or lightning-coexistence run.
- There are no per-step MPI collectives in the chemistry error path.
- Standalone exact-grid validation remains a pre-launch check, and the selected MIEM adapter independently validates inventory metadata against rank-local MPAS IDs and geometry after the first read and before any MICM mutation.
- No implementation checkpoint advances until its verified commit is present on the remote target branch.

## Final completion checklist

- [x] Exact MUSICA and MIEM commits are pinned and reproducible; no required sibling-repo or generated pkg-config fix is only local.
- [x] The exported MUSICA static-link closure pulls MIEM and its NetCDF-C dependency in linkable order, with optional libraries and the C++ runtime selected by the dependency build.
- [x] Disabled-path baseline hashes were captured before implementation with the same pinned dependency, compiler, precision, and inputs used for E0.
- [x] Preprocessing produces a validated global inventory in exact MPAS order.
- [x] The mesh fingerprint is canonically specified, shared by both tools, and covers spherical or planar geometry as appropriate.
- [x] Wrong-order or wrong-geometry inventories are detected even when `nCells` matches and planar latitude/longitude are all zero.
- [x] The canonical chem-box mesh, initialized state, and 8-rank partition are tracked, hashed, documented, and reproducibly regenerable with pinned tools.
- [x] `config_miem_file` is the sole Phase 1 runtime switch.
- [x] Empty configuration preserves existing behavior and output.
- [x] MIEM lifecycle is owned by `mpas_miem.F` and uses only the public Fortran API.
- [x] Global inventory cells map to owned MPAS cells through `indexToCellID` on 8 ranks.
- [x] Every MIEM species maps one-to-one to a writable MICM species and `EMIS.*` parameter.
- [x] Runtime emission diagnostic names are queried from `config_micm_file`, gated by nonempty `config_miem_file`, and cross-matched against actual MIEM output species.
- [x] Surface flux units and lowest-layer conversion are verified analytically.
- [x] Surface-only inventories leave upper-level emission parameters zero; normalized vertical profiles populate only their declared layers and close exactly to the column source.
- [x] Rates remain fixed across chemistry substeps and are applied to both MICM states.
- [x] Gregorian epoch handling, interpolation, and out-of-range failures are tested.
- [x] Diagnostics and finalize mass totals agree with the applied source.
- [x] R0-R5 are tracked, automated 8-rank scenarios, and each produces a schema-valid passing throughput JSON report.
- [x] R2 closes the complete inventory-to-diagnostic-to-model-reported-source-to-tracer-mass chain; reactive scenarios apply only the scientifically valid source-accounting assertions.
- [x] Continuous and restart runs agree at the default chemistry cadence.
- [x] MIEM and lightning NOx coexist without an implicit replacement or hidden double count.
- [x] Clean MUSICA and non-MUSICA builds pass.
- [x] Full MPAS smoke and regression tests pass with 8 MPI ranks.
- [x] Build, run, preprocessing, architecture, API, and limitation documentation is complete.
- [x] Every completed phase, stage, and milestone has a focused verified commit pushed to `develop_emissions`, with its remote SHA recorded.
- [x] Selected-cell MIEM I/O, runtime grid validation, vertical profiles, bounded disaggregated diagnostics, and production-mesh benchmarks pass the activated Phase 7 gate.
- [x] The verified MIEM spatial, layered, and 30-minute budget plots, their
  SHA-256 manifest, and the Phase 8 checkpoint are present on
  `origin/develop_emissions`.
- [x] A science-grade NO/NO2 inventory is acquired, chemically mapped,
  conservatively remapped, exact-grid packaged, validated, and externally
  retained with complete provenance.
- [x] Global G0-G4 shakedowns exercise dynamics, transport, reactive chemistry,
  TUV-x, and MIEM through `atmosphere_model` and pass their promotion gates.
- [x] A full-diurnal global science run, restart trajectory, and matched control
  pass source, chemistry, dynamics, performance, and reproducibility gates.
- [x] Every Phase 9 stage and final checkpoint is committed, pushed, and
  remote-SHA verified without committing large inventory or run files.
