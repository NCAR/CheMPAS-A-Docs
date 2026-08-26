# MIEM implementation checkpoint log

This log records delivered checkpoints for `docs/chempas/mvp/PLAN_EMISSIONS.md`. Large run
artifacts remain outside the repository; their locations and hashes are stored
in the referenced machine-readable manifests.

## Phase 0 — pinned dependency and disabled baseline

- Date: 2026-08-05
- Branch: `develop_emissions`
- Phase checkpoint: `1c72970653158b1d218289b15868281e6a420c0f`
- Remote verification: `origin/develop_emissions` resolved to the same SHA
- Disabled-baseline checkpoint: `96b25e0825d4d6f26aa4c2470ba7e102dc293d3f`
- Baseline manifest: `test_cases/miem_disabled_baselines.json`
- Baseline artifact root:
  `/home/fillmore/Data/CheMPAS/baselines/miem-disabled-phase0-4eb4e677-musica-764c912f`

Pinned dependency revisions:

| Component | Revision |
|---|---|
| MUSICA-Fortran | `764c912fcc37068117db83b7133253a48eceadc4` |
| MICM | `bb57684a2047f0e58f30b199366294af879e8597` |
| MIEM | `2bb1e21dc251e3eb356fd0a2d4ae74f7fc145150` |
| MechanismConfiguration | `fa06d8c6305172f62e6350ed5cd3a4cbfcd519ee` |
| TUV-x | `bbf7dd9a144fa0f0294b3779f3f993818638e20c` |

Verified environment: GNU Fortran 15.2.0, NetCDF-C 4.10.1,
NetCDF-Fortran 4.6.3, PnetCDF 1.14.1, double precision, and 8 MPI ranks for
all captured model cases.

Verification performed:

- `scripts/check_build_env.sh` in report and export modes: pass.
- Constructor-level MICM+MIEM probe using only `pkg-config` flags: pass.
- The same constructor probe with every exported `-lnetcdf` removed: expected
  link failure with unresolved `nc_*` symbols.
- Fresh isolated `make -j8 gfortran ... MUSICA=true`: pass; the final
  atmosphere executable linked against MUSICA-Fortran 0.16.5.
- Stale/version-only pkg-config metadata: rejected before compilation.
- `python -m unittest -v tests.test_hash_netcdf_fields`: 3 tests passed.
- `bash -n scripts/check_build_env.sh` and `git diff --check`: pass.
- MUSICA checkout contained no uncommitted tracked changes.
- Baseline ABBA, Chapman, and lightning-NOx runs completed on 8 ranks and
  recorded 195 scientific-field hashes in the tracked manifest.

## Phase 1 — exact-grid inventory preparation and chem-box assets

- Date: 2026-08-05
- Branch: `develop_emissions`
- Inventory-tooling checkpoint: `3f2adb643904cc0bf0b3ff13742c00e3cdc86e3a`
- Phase checkpoint: `3f6ddda22f8c56bc720758df6163b543ec94af5e`
- Remote verification: `origin/develop_emissions` resolved to the phase SHA
- Mesh fingerprint algorithm: `chempas-mesh-sha256-v1`
- Inventory format: NetCDF-4, exact-grid, `UPTEMPO` time coordinate
- Canonical asset source: MPAS-Tools 2.0.0 at
  `4b5c11b4be471498da36a2637ad1cf49962b3d05`
- Canonical init source: CheMPAS planning baseline at
  `4eb4e6772c62bbc42453d91ca2010f2bea4935c6`

Tracked canonical asset hashes:

| Asset | SHA-256 |
|---|---|
| `chem_box_grid.nc` | `89c5338ea39a165a5655ea82ae0c6d0bf7f8fbe87069ddd2a667fa60f5b185ad` |
| `chem_box_init.nc` | `88b9210f8993dfbdbbb6ccb49bfe466cf6de58f32ab017c0fc4d69dd2ed0e931` |
| `chem_box.graph.info.part.8` | `d587ff5150e846e2b629961c9decb7e96f29cc115dc0d1f2e433a28844cd90d4` |

Verification performed:

- Two independent official MPAS-Tools generations produced byte-identical
  canonical grid, init, and 8-rank partition assets.
- The asset regeneration script's pinned-manifest verification passed.
- Zero, constant, and deterministic cell/time-signature inventories were
  regenerated twice and were byte-identical.
- All three inventories passed the strict standalone validator against the
  canonical init mesh and their expected SHA-256 digests.
- Negative checks reject cell-count mismatches, planar and spherical
  coordinate permutations, zero-valued planar coordinate substitutions, ID
  permutations, and insufficient time coverage.
- `python -m unittest -v tests.test_miem_mesh_identity
  tests.test_miem_inventory tests.test_miem_fixture`: 12 tests passed.
- Shell syntax, Python byte compilation, and `git diff --check`: pass.

### Phase 1 fixture-time correction

- Date: 2026-08-05
- Checkpoint: `cf3f81f1482ce57223e0c1f928fa8bd2269cc043`
- Remote verification: `origin/develop_emissions` resolved to the same SHA
- Previous init asset SHA-256:
  `88b9210f8993dfbdbbb6ccb49bfe466cf6de58f32ab017c0fc4d69dd2ed0e931`
- Corrected init asset SHA-256:
  `7a02d9b8834cdd0ecef95b8554fb355358e71525ce94c4b2995618f2fae93759`

The first Phase 2 staging run detected that the tracked atmosphere namelist
started at `2026-06-22_12:00:00`, while the canonical init file retained the
legacy `0000-01-01_18:00:00` timestamp. The init namelist and canonical state
now use the first synthetic-inventory timestamp. The normative mesh identity
is unchanged at
`245e22405209483523b7de67f38220b331c1f2944817d03423cf4ac09b7db388`.

Verification performed:

- Two independent 8-rank init runs produced byte-identical corrected assets.
- The tracked asset manifest passed.
- All 12 mesh-identity, inventory, and fixture tests passed with unchanged
  deterministic fixture hashes.

## Phase 2 — MIEM adapter, configuration, and lifecycle

- Date: 2026-08-05
- Branch: `develop_emissions`
- Adapter checkpoint: `d531774f0e87e446074ee6f96188cd19a86ff694`
- Lifecycle checkpoint: `ade1886b34e3a093ee2f4006eeaf2008aa34a078`
- Phase checkpoint: `c410b171cbbe8769013842e0001f82a0f271035b`
- Remote verification: `origin/develop_emissions` resolved to the phase SHA
- Clean MUSICA build root: `/tmp/chempas-phase2-gate.BVzrxt`
- Clean non-MUSICA build root: `/tmp/chempas-phase2-nomusica.ELffYi`
- Runtime artifact root: `/tmp/chempas-phase2-runs.AW2eB2`

Verification performed:

- A fresh isolated `make -j8 ... MUSICA=true` compiled and linked the
  atmosphere executable with `mpas_miem.o` in the chemistry archive.
- A separate fresh isolated `make -j8 ...` without MUSICA compiled and linked
  successfully, confirming that the guarded lifecycle additions do not affect
  the non-MUSICA core.
- An 8-rank disabled run completed, logged exactly one rank-zero
  `[MIEM] Disabled` message, and did not read an inventory.
- An 8-rank enabled run constructed a 64-cell, two-species MIEM object on all
  ranks and consistently enumerated `NO` and `NO2` without per-cell logging.
- An enabled `gregorian_noleap` run failed during initialization with the
  expected `[Chemistry] [MIEM]` calendar error.
- A targeted 63-cell-inventory construction run established that the pinned
  MIEM implementation defers inventory file and cell-count validation until
  its first `run` call. The executable wrong-count failure is consequently
  carried as the first Phase 3 runtime gate, before MICM state mutation.
- `git diff --check` passed, and all Phase 2 implementation checkpoints were
  pushed and verified before Phase 3 began.

## Phase 3 — MIEM surface fluxes coupled through MICM

- Date: 2026-08-05
- Branch: `develop_emissions`
- MICM mapping/rate-setter checkpoint:
  `da87d123599be8e6818e4320f2cb693d3e64d921`
- Chemistry-step checkpoint: `b14602496d7d677b50729bc9a3aaa7c57cf0b65e`
- Contract-test checkpoint: `c1a10ddf2ac2a0647e499da9628d33644f15f53e`
- Phase checkpoint: `909f47fb65eff08efe65df41d3a9fb923c146050`
- Remote verification: `origin/develop_emissions` resolved to the phase SHA
- Clean build root: `/tmp/chempas-phase3-runtime-build.UGsB7v`
- Runtime artifact root: `/tmp/chempas-phase3-runs.4RbJ13`

Verification performed:

- A fresh isolated MUSICA-enabled build compiled and linked the new emission
  bookkeeping, MPAS time conversion, MIEM call, and MICM rate-setting path.
- The pinned MUSICA parser exposed exactly `EMIS.NO` and `EMIS.NO2` from the
  emissions-only `micm_configs/miem_nox.yaml` mechanism.
- `scripts/test_musica_emission_contracts.sh` passed against the clean build,
  exercising valid conversion plus dimension mismatch, missing species,
  missing `EMIS.*`, duplicate species, invalid molar mass, negative/nonfinite
  flux, and invalid lowest-layer thickness failures.
- The 8-rank zero-flux case produced exactly zero `qNO` and `qNO2` changes.
- The 8-rank constant case produced only the expected dominant level-1 source
  response, with a 9:1 NO:NO2 mass response and the expected analytical
  surface-source tendency within the dynamics-coupled tolerance.
- One and four MICM substeps produced bitwise-identical final `qNO` and `qNO2`
  arrays for the same three-second chemistry interval.
- The reference-state run logged identical coupled/reference NO and NO2
  concentrations before transport-induced divergence.
- The deferred 63-cell inventory test failed on the first MIEM call with:
  `file 'miem_inventory.nc' has 63 cells but host expects 64`.
- A coexistence smoke run kept MIEM enabled while the existing lightning-NOx
  source independently activated 72 cell-levels.
- The rank-zero timer report contained one `chem MIEM` call per chemistry
  solve, and `git diff --check` and shell syntax checks passed.

## Phase 4 — runtime flux diagnostics and integrated source budgets

- Date: 2026-08-05
- Branch: `develop_emissions`
- Diagnostic-discovery checkpoint:
  `4223ed46b96ebd70b3f4c6216a209b1a20559d18`
- Phase checkpoint: `e59d10107a0d939930e272296035db83548b48ca`
- Remote verification: `origin/develop_emissions` resolved to the phase SHA
- Clean build root: `/tmp/chempas-phase3-runtime-build.UGsB7v`
- Constant-flux runtime root: `/tmp/chempas-phase4-runtime.RiT80O`
- Cell-signature runtime root: `/tmp/chempas-phase4-signature.CpUgLb`
- Disabled runtime root: `/tmp/chempas-phase4-disabled.9qPHaJ`

Verification performed:

- A MUSICA-enabled double-precision atmosphere build compiled and linked the
  runtime field publication and finalize-only MPI reduction path.
- `scripts/test_musica_emission_contracts.sh` passed against that build.
- An 8-rank run with distinct MICM and MIEM YAML files discovered `EMIS.NO`
  and `EMIS.NO2` only from MICM while the MIEM mechanism section remained
  empty; photolysis was disabled throughout the run.
- Initial `emis_NO` and `emis_NO2` fields were bitwise zero. Final constant
  fields were exactly `9.0e-13` and `1.0e-13 kg m-2 s-1` in all 64 cells,
  with an exact 9:1 ratio.
- The cell/time-signature run reproduced `0.9 * nox_anth_sum` and
  `0.1 * nox_anth_sum` exactly at every global cell, demonstrating that
  rank-owned publication assembles in global-ID order.
- Rank-zero finalize totals were `3.74122974434877e-05 kg` for NO and
  `4.15692193816530e-06 kg` for NO2. Both agreed with the independently
  evaluated global `sum(flux * areaCell * dt)` to no worse than
  `1.23e-15` relative error.
- The 8-rank empty-`config_miem_file` run added no `emis_*` fields, opened no
  inventory, had no `chem MIEM` timer, and reported zero critical errors.
- `git diff --check` passed, the phase checkpoint was pushed, and the local
  and remote branch SHAs matched before Phase 5 began.

## Phase 5 — throughput harness and complete chem-box matrix

- Date: 2026-08-05
- Branch: `develop_emissions`
- Harness checkpoint: `04c69efc82754c9a90d9b51fc544fddbf44634ef`
- Phase checkpoint: `decf4952e41a588554102f514d8dd726a88920eb`
- Remote verification: `origin/develop_emissions` resolved to the phase SHA
- Initial matrix executable: `/tmp/chempas-phase3-runtime-build.UGsB7v/atmosphere_model`
- Phase-gate clean build root: `/tmp/chempas-phase5-gate.OtCF69`
- Passing report root: `/tmp/chempas-miem-integration-yclnzs2v/reports`

Verification performed:

- All 15 MIEM mesh-identity, inventory, fixture, and throughput unit tests
  passed, along with Python compilation, shell syntax, and diff checks.
- R0-R5 completed with 8 MPI ranks. R3 passed at the inventory start,
  midpoint, and endpoint, and R4 passed continuous, four-substep, and
  split/restart comparisons.
- Every scenario emitted a schema-valid passing JSON report. R2 closed the
  inventory-to-diagnostic-to-finalize-log-to-tracer mass chain, while R5
  independently activated lightning NOx in 72 cell-levels.
- The focused MPI adapter test produced identical global-ID mappings with one
  and eight ranks.
- Repository preflight passed in report and export modes, including the
  emissions-constructor static-link probe. A detached worktree at the matrix
  checkpoint was fully cleaned and rebuilt with `make -j8 gfortran`, MUSICA,
  and double precision; the MICM emissions contract executable passed against
  the resulting fresh archives.
- The E12 negative gate passed missing-file, 63-vs-64-cell, out-of-range-time,
  and invalid-calendar cases with expected failures in eight-rank MPAS runs.
  The focused contract covered missing species, missing `EMIS.*`, negative and
  nonfinite fluxes, and invalid lowest-layer thickness.
- The positive harness now audits all produced rank logs for zero MPAS error
  summaries, MIEM inconsistency terms, and exactly one enabled or disabled
  lifecycle plus timer row. Four focused log-audit tests and the full 19-test
  MIEM Python suite passed.
- The harness removed 11 successful generated run directories and retained
  the eight compact JSON reports listed by the successful run.
- The clean-build matrix was repeated with the strict log audit and passed;
  its reports are in `/tmp/chempas-miem-integration-y1unx1bw/reports`.
- The E0 harness verified the pinned dependency, compiler, configuration, and
  input identities, then reran ABBA, Chapman-NOx, and lightning-NOx with eight
  ranks. Every canonical scientific-field digest matched the Phase 0 baseline
  bitwise, with no `emis_*` field or inventory access. Three compact reports
  remain in `/tmp/chempas-miem-e0-kavelnoz/reports`; the successful generated
  run directories, including their multi-gigabyte outputs, were removed.
- Full repository Python discovery passed all 27 tests. The canonical asset
  manifest and all 11 retained Phase 5 JSON reports were rechecked, and
  `git diff --check` passed with no generated run or dependency artifact
  staged. Two diagnosed failure-harness development workspaces were moved to
  the system trash and remain recoverable.

## Phase 6 — documentation and release readiness

- Date: 2026-08-06
- Branch: `develop_emissions`
- Documentation milestone: `c814ca2086f573d597f08f0de2c81a8cefe4f879`
- Phase checkpoint: `c11b1aec37fb5e4655c108825d973a6954d13cb5`
- Remote verification: `origin/develop_emissions` resolved to the phase SHA
- Documentation-gate report root:
  `/tmp/chempas-miem-integration-t5gac1od/reports`

Verification performed:

- The normative MIEM guide now covers exact-grid preprocessing and validation,
  UPTEMPO and mesh-fingerprint contracts, distinct MICM/MIEM configuration,
  source conversion, diagnostics, source accounting, R0-R5, disabled
  baselines, lightning coexistence, and replicated-I/O limitations.
- Build, run, architecture, component, MUSICA API/integration, namelist, and
  test-case references use the same tested filenames, switches, species, and
  units and link to the normative guide.
- Four documentation contract tests passed, including every local link,
  Registry/namelist consistency, required workflow terms, and the rule that
  documentation cannot claim runtime regridding.
- Full repository Python discovery passed all 31 tests.
- The canonical mesh/init/partition manifest passed verification.
- The documented `constant_flux` workflow ran on eight MPI ranks with the
  Phase 5 clean-build executable, produced a schema-valid passing throughput
  report, and confirmed identical one-rank/eight-rank global-ID mappings.
- `git diff --check` passed, no generated run data was staged, and the
  documentation milestone was pushed and matched `origin/develop_emissions`.

## Phase 7 — activated scalability work

- Activation date: 2026-08-06
- Branch: `develop_emissions`
- Scalability-design checkpoint:
  `ac820f07c7aa216b44f57514219b19b077575a50`
- Remote verification: `origin/develop_emissions` resolved to the design SHA

The activated design specifies one-based selected-cell ordering, coalesced
NetCDF hyperslabs, independent per-rank ownership, runtime inventory metadata,
normalized vertical profiles, bounded sector/category diagnostics, the
decision to retain `regridding: none`, and regional/global production-mesh
benchmark evidence. Five documentation contract tests and `git diff --check`
passed before the checkpoint was pushed.

### MechanismConfiguration vertical-profile stage

- Upstream branch: `NCAR/MechanismConfiguration:feature/miem-scalability`
- Checkpoint: `82c159ae6d74934318ffd6c405a45c2159065b12`
- Remote verification: the upstream branch resolved to the checkpoint SHA
- Clean build root: `/tmp/mechconfig-phase7.3RNTr4`

The v1 emissions schema now accepts `vertical injection: profile` only with a
nonempty finite, nonnegative `vertical profile` whose fractions sum to one.
Surface sources remain backward compatible and plume-rise remains rejected.
The clean GNU 15.2 build and all 34 CTest tests passed, including normalized
profile parsing and missing, empty, negative, non-unit, and surface/profile
conflict failures.

### MIEM selected-cell I/O milestone

- Upstream branch: `NCAR/miem:feature/miem-scalability`
- Checkpoint: `3509a6b4c82244f7f66499650605f7b853044d91`
- Remote verification: the upstream branch resolved to the checkpoint SHA
- Clean build root: `/tmp/miem-selected-phase7.uWTIUB`

MIEM now accepts a validated, one-based ordered list of global inventory cells.
The ECCAD and UPTEMPO readers sort that request into maximal contiguous runs,
read each run with `nc_get_vara`, and scatter values back into host order;
an empty selection retains the existing full-grid behavior. The clean Debug
double-precision build passed all 13 CTest tests, including invalid and
duplicate selections, nonmonotonic host ordering, and bitwise equality between
full-grid and selected results.

### MIEM exact-grid metadata milestone

- Upstream branch: `NCAR/miem:feature/miem-scalability`
- Checkpoint: `68fadc0839a79f949be81667433c84dd0913c898`
- Remote verification: the upstream branch resolved to the checkpoint SHA
- Clean build root: `/tmp/miem-metadata-phase7.m2z97Z`

MIEM now exposes immutable inventory geometry and fingerprint metadata after
the first file open. In selected mode it reads only the requested
`indexToCellID`, `areaCell`, and available coordinate hyperslabs in host order
and requires the exact-grid algorithm, digest, manifest, geometry flags, and
geometry-required fields. Metadata fields retain file double precision,
legacy full-grid inventories remain supported without metadata, and differing
metadata across sources or later files is fatal. The clean GNU 15.2 Debug
double-precision build passed all 13 CTest tests, including planar/spherical
ordering, missing-metadata rejection, and conflicting-source rejection.

### MIEM vertical-profile flux milestone

- Upstream branch: `NCAR/miem:feature/miem-scalability`
- Checkpoint: `2deb44bc429ad1f5bef1fe5eb4d46b864cf5232e`
- Remote verification: the upstream branch resolved to the checkpoint SHA
- Clean double build root: `/tmp/miem-vertical-phase7.Stiw2l`
- Clean float build root: `/tmp/miem-vertical-float-phase7.yAkF8u`

MIEM now accepts fixed normalized source profiles with exactly one fraction per
model level while retaining level-1 behavior for surface sources and rejecting
plume rise. Hierarchy selection chooses a source before its profile is
applied; `layer_flux_` therefore preserves source identity and closes to the
column-integrated surface flux after category summation. The tendency
converter handles every populated layer and retains a legacy surface-state
path. Clean GNU 15.2 Debug builds in double and float precision each passed
all 13 CTest tests, including validation failures, winner-profile semantics,
category closure, per-level conversion, and column mass reconstruction.

### MIEM bounded-diagnostics and completed upstream stage

- Upstream branch: `NCAR/miem:feature/miem-scalability`
- Checkpoint: `9fdf14a189262eecb677862d877ab72b06c95e21`
- Remote verification: the upstream branch resolved to the checkpoint SHA
- Clean double build root: `/tmp/miem-diagnostics-phase7.RfK7oH`
- Clean float build root: `/tmp/miem-final-float-phase7.DLUz9s`
- Install/export root: `/tmp/miem-install-phase7.6SK065`

MIEM now allocates no disaggregated diagnostics by default. An explicit
`DiagnosticSelection` may request known unique sectors and categories, opt in
to layered buffers, and must satisfy the hard
`species * groups * levels` field cap. Group values follow the same hierarchy
winner as totals, selected category columns close to totals when all
categories are requested, and every layered group closes to its column. The
clean GNU 15.2 Debug builds in double and float precision each passed all 13
CTest tests. A clean install exported the new cell-selection, exact-grid
metadata, vertical-layer, and diagnostic-selection public headers and CMake
package. This checkpoint completes the activated MIEM upstream implementation
stage; MUSICA is pinned to this exact revision in the next stage.

### MUSICA dependency-pin milestone

- Upstream branch: `NCAR/musica:feature/miem-scalability-fortran`
- Checkpoint: `e50da95f5774f6c51219bc4d89d500463a7d4cf3`
- Remote verification: the upstream branch resolved to the checkpoint SHA

MUSICA now pins MechanismConfiguration
`82c159ae6d74934318ffd6c405a45c2159065b12` and MIEM
`9fdf14a189262eecb677862d877ab72b06c95e21`. Both dependency branch refs were
resolved from their remotes before this focused pin commit was pushed.

### MUSICA C++ scalability-wrapper milestone

- Upstream branch: `NCAR/musica:feature/miem-scalability-fortran`
- Checkpoint: `61394e718d7df9e180f2d44633d65574d6ff074b`
- Remote verification: the upstream branch resolved to the checkpoint SHA
- Clean build root: `/tmp/musica-cxx-phase7.8H8Byk`

MUSICA now preserves parsed normalized vertical profiles and offers a
backward-compatible `EmissionsOptions` construction path for ordered selected
global cells and bounded diagnostics. Its C++ wrapper exposes global/local
dimensions, selected IDs, column and layered flux buffers, requested
sector/category buffers, and immutable exact-grid metadata after a successful
run. The focused GNU 15.2 Debug gate passed 20 tests covering the translator,
synthetic selected-cell scalability API, field-cap rejection, both real
inventory end-to-end paths, and the unchanged legacy C API. The repository's
pre-existing untracked self-referential `configs/v1/chapman/chapman` symlink
prevents CMake's all-target config-copy step; tests were therefore built as
explicit targets and run from the source root without modifying that unrelated
user file.

### MUSICA C scalability-ABI milestone

- Upstream branch: `NCAR/musica:feature/miem-scalability-fortran`
- Checkpoint: `5b1e0d884ae3c77472bfb4b23cf68857dfbcd4b1`
- Remote verification: the upstream branch resolved to the checkpoint SHA
- Clean build root: `/tmp/musica-cxx-phase7.8H8Byk`

The C ABI now retains `CreateEmissions` and adds a selected-cell constructor
with explicit bounded diagnostic selection. Stable queries expose global,
local, and vertical dimensions; selected IDs; species/level/cell layer
buffers and strides; ordered sector/category buffers; and exact-grid scalar,
string, index, coordinate, and units metadata. Pointers are refreshed or
queried under documented object/run lifetimes, and null selected arrays fail
through the C error channel. All eight C-ABI tests passed, including a
synthetic two-source, three-level, nonmonotonic selected-cell run and the
legacy full-grid NO/NO2 cases.

### MUSICA Fortran scalability-API milestone

- Upstream branch: `NCAR/musica:feature/miem-scalability-fortran`
- Checkpoint: `1403e3d22717bc87f3bf9d0aa591caf039c92bbc`
- Remote verification: the upstream branch resolved to the checkpoint SHA
- Clean build root: `/tmp/musica-fortran-phase7.9fBg4s`

The public `musica_emissions` module retains its full-grid constructor and now
overloads construction with ordered one-based selected cell IDs, optional
sector/category requests, optional layered diagnostics, and a hard field cap.
It reports global/local/vertical dimensions and refreshes all C-owned column,
layer, diagnostic, selected-ID, and exact-grid metadata pointers after every
successful run. The Fortran integration test generates a deterministic exact
UPTEMPO inventory in its isolated build directory, so no NetCDF binary is
committed. A clean GNU 15.2 C/C++/Fortran build passed the legacy full-grid and
new selected Fortran paths (including cap rejection and repeated-run pointer
refresh), all eight C-ABI tests, both C++ scalability tests, eleven translator
tests, and both real-inventory end-to-end tests. This completes the upstream
MUSICA binding stage.

### CheMPAS dependency-pin and preflight milestone

- MUSICA checkpoint: `1403e3d22717bc87f3bf9d0aa591caf039c92bbc`
- MIEM checkpoint: `9fdf14a189262eecb677862d877ab72b06c95e21`
- MechanismConfiguration checkpoint: `82c159ae6d74934318ffd6c405a45c2159065b12`
- MICM checkpoint: `bb57684a2047f0e58f30b199366294af879e8597`
- TUV-x checkpoint: `bbf7dd9a144fa0f0294b3779f3f993818638e20c`
- Clean MUSICA install build root: `/tmp/musica-install-phase7.laGpuu`
- Installed prefix:
  `/home/fillmore/software/musica-1403e3d22717bc87f3bf9d0aa591caf039c92bbc`

CheMPAS now requires the pushed Phase 7 MUSICA, MIEM, and
MechanismConfiguration revisions in its Makefile, environment preflight,
integration-report provenance, and build documentation. The clean Release
MUSICA install used GNU 15.2 MPI wrappers with Fortran, MPI, MICM, MIEM, and
TUV-x enabled and used `FETCHCONTENT_TRY_FIND_PACKAGE_MODE=NEVER` to retain the
tested bundled dependency graph. Both report and export preflight modes passed.
The generated constructor probe imported `musica_micm` and
`musica_emissions`, constructed both objects, and linked using only
`pkg-config --cflags --libs musica-fortran`; the exported static closure placed
MIEM before NetCDF-C and selected `libstdc++` from the recorded compiler
metadata. `git diff --check`, shell/Python syntax checks, and all 32 repository
Python unit tests also passed.

### CheMPAS selected-cell runtime milestone

- Checkpoint: `228d09b8fb61d7ae7dd84d7f6083eca1cb09ab09`
- Remote verification: `origin/develop_emissions` resolved to the checkpoint SHA

CheMPAS now constructs one MIEM object per rank with only the ordered owned
`indexToCellID` selection and the actual MPAS vertical-level count. The adapter
retains only rank-local expected geometry, verifies the returned selected-cell
ordering and dimensions, and validates exact inventory grid metadata after the
first MIEM read and before returning any flux for MICM mutation. It copies both
column and per-layer fluxes into owned-cell order, rejects invalid values or
layer/column closure failures, and converts every populated layer into matching
coupled and reference MICM emission rates.

The MUSICA link directory is now placed before broad PIO and NetCDF library
directories so an older same-named archive cannot shadow the pinned package
whose modules and pkg-config metadata passed preflight. A clean GNU 15.2,
double-precision, MUSICA-enabled atmosphere build passed against the exact
installed MUSICA prefix. The focused MPI mapping test proved identical global-ID
results on one and eight ranks and rejected independently perturbed area,
geometry class, and local geometry order in-model. The full eight-rank MPAS R3
cell/time-signature scenario passed start, midpoint, end, and all throughput
checks. The MUSICA emission-contract test, all 32 Python unit tests, shell/Python
syntax checks, and `git diff --check` also passed.

### CheMPAS bounded layered-diagnostics milestone

- Checkpoint: `721ead3395a92f02be6eb5fc474bdad02c5dbcc4`
- Remote verification: `origin/develop_emissions` resolved to the checkpoint SHA

CheMPAS now parses explicit sector and category selections, rejects duplicate,
unknown, colliding, overlength, and over-cap requests, and registers only the
requested runtime fields. The definitive
`species * groups * levels` cap check runs after the mesh supplies
`nVertLevels` but before MPAS field allocation. Total and selected-group column
diagnostics retain `kg m^{-2} s^{-1}` units; opt-in layered forms use the same
units per model layer and are published only after a successful chemistry
transaction.

The GNU 15.2 double-precision MUSICA-enabled atmosphere build passed against
the exact installed MUSICA prefix. The focused adapter passed on one and eight
ranks, including parser, sanitizer, upstream over-cap, unknown-sector, mapping,
metadata, and group/layer closure checks. The eight-rank R6 run applied the
tracked 60-level `[0, 0.25, 0.75, 0, ...]` profile and produced a schema-valid
report closing column flux, layered flux, sector/category families, finalize
mass logs, and dry NO/NO2 tracer mass. A 240-field request with a cap of 239
failed during derived-dimension setup before the MPAS field-allocation phase.
All 32 Python unit tests and `git diff --check` also passed.

### CheMPAS distributed regression milestone

- Checkpoint: `a0ca616c40372eea4207f6f5ab16037ac632e9ed`
- Remote verification: `origin/develop_emissions` resolved to the checkpoint SHA

The focused adapter now compares the selected-cell path bit-for-bit with the
retained full-grid constructor at the two inventory endpoints, both midpoints,
and the final endpoint, on both one and eight MPI ranks. It also retains the
global-ID mapping, exact-grid metadata, parser, diagnostic-selection, and
group/layer closure assertions. The MICM contract executable now exercises
valid multi-level conversion plus wrong-shape, negative, nonfinite, and invalid
upper-layer failures.

The eight-rank runtime-failure gate now bypasses standalone validation to prove
that corrupted in-file `xCell` metadata fails in the adapter before MICM
mutation. It also proves that a 240-field diagnostic request with a cap of 239
fails before MPAS field allocation, alongside missing-file, wrong-count,
out-of-range-time, and invalid-calendar cases. The complete R0-R6 matrix passed
12 eight-rank launches and produced nine schema-valid throughput reports. All
three larger MIEM-disabled E0 cases—supercell ABBA, global Chapman-NOx, and
supercell lightning—remained bitwise identical to their pinned scientific
field manifests. All 32 Python unit tests, syntax checks, and
`git diff --check` passed.

### CheMPAS production-mesh scalability benchmark milestone

- Checkpoint: `04d201467a19ce9dbe2e451339de472c28573e44`
- Remote verification: `origin/develop_emissions` resolved to the checkpoint SHA
- Regional report SHA-256:
  `3fe852d49864fe2def35fff77b8a773ee9390c7f092f44f7923ef85765f9f070`
- Global report SHA-256:
  `0fb74d7dc15c55b9c671b6705deaeac8fe1539d2336c440b0b5c9da1c8835a39`

The public MUSICA Fortran benchmark ran replicated full-grid and selected-cell
modes with eight MPI ranks on the external 28,080-cell, 60-level planar
supercell asset and the external 40,962-cell, 26-level spherical x1.40962
asset. For each mesh it generated and packaged a temporary deterministic
two-time, two-species exact-grid inventory; no external run data or generated
inventory was committed and `regridding: none` remained mandatory.

Every rank's 13-sample `(sample, global ID, NO, NO2)` stream was bitwise equal
between modes. Selected ranks reported only their owned `object_cells`. Across
all ranks, selected payload and modeled persistent cell-indexed state were
exactly one eighth of replicated totals: regional payload was 2,471,040 versus
19,768,320 bytes and state was 3,762,720 versus 30,101,760 elements; global
payload was 3,604,656 versus 28,837,248 bytes and state was 2,703,492 versus
21,627,936 elements. The schema-valid reports also record coalesced hyperslab
counts, construction and first-open time, 12-sample warm-step time, peak RSS,
input/output hashes, compiler, and dependency revisions. All 36 Python unit
tests, script syntax checks, report-contract tests, and `git diff --check`
passed before the benchmark checkpoint was pushed and its remote SHA verified.

### CheMPAS Phase 7 documentation milestone

- Checkpoint: `01f03dde0bad85e7c8e6073f3ccc010f38fefeb7`
- Remote verification: `origin/develop_emissions` resolved to the checkpoint SHA

The build and run guides, architecture/component descriptions, MUSICA
integration and public-API reference, normative MIEM workflow, scalability
design, model namelist appendix, chemistry-coupling guide, MIEM configuration
and chem-box references, Registry option metadata, and plan now describe the
implemented selected-cell path. They cover external versus generated data,
coalesced rank-local reads, first-read exact-grid validation, surface and
normalized-profile conversion, bounded total/layer/sector/category fields,
R0-R6 and negative gates, production benchmark reproduction, and the retained
no-runtime-regridding boundary.

Six focused documentation contracts verified every local link, all five MIEM
namelist options, the complete workflow vocabulary, absence of superseded
replicated-runtime claims, and both versioned production reports. Full Python
discovery passed all 37 tests; syntax checks and `git diff --check` also passed
before the focused documentation commit was pushed and remote-verified.

### CheMPAS Phase 7 clean release-gate milestone

- Final phase checkpoint: `b8e7d3764faa5c89242d0a4c30ce9d65c5f549d2`
- Remote verification: `origin/develop_emissions` resolved to the checkpoint SHA
- Clean dependency build roots: `/tmp/mechconfig-phase7.3RNTr4`,
  `/tmp/miem-diagnostics-phase7.RfK7oH`, and
  `/tmp/miem-final-float-phase7.DLUz9s`
- Clean MUSICA build/install roots: `/tmp/musica-fortran-phase7.9fBg4s` and
  `/tmp/musica-install-phase7.laGpuu`
- CheMPAS MUSICA build log: `/tmp/chempas-phase7-final-musica-build.log`
- CheMPAS non-MUSICA build log:
  `/tmp/chempas-phase7-final-nomusica-build.log`
- R0-R6 report root: `/tmp/chempas-phase7-final-reports.5Ok4Fg`
- E0 report root: `/tmp/chempas-miem-e0-ee4tn3c4/reports`

The final GNU 15.2 preflight resolved all five exact dependency revisions,
verified the exported MIEM-before-NetCDF static closure, and linked the
MICM-plus-emissions constructor probe using only MUSICA pkg-config flags. Clean
double-precision, MPI-enabled CheMPAS builds passed with `MUSICA=true` and
`MUSICA=false`; the latter link line contained no MUSICA or MIEM library and
the resulting executable had no unresolved or dynamic MUSICA/MIEM dependency.
Its one MIEM-named internal symbol is the intentional compile-time-disabled
diagnostic-selection wrapper, which returns the documented MUSICA-required
error without calling an external library.

The final MUSICA executable passed the MICM source-rate contract; selected
versus full-grid and one-rank versus eight-rank comparisons at five inventory
samples; all nine schema-valid R0-R6 throughput reports; and all six eight-rank
failure cases for missing files, cell count, time coverage, calendar, exact-grid
metadata, and the diagnostic field cap. NO and NO2 output diagnostics, applied
source logs, and emissions-only tracer mass retained the R2 end-to-end closure;
the normalized multi-level and bounded group diagnostics retained their R6
column closures. The three larger disabled cases—supercell ABBA, global
Chapman-NOx, and supercell lightning—again matched their E0 scientific-field
manifests bit-for-bit.

All 37 Python tests, shell and Python syntax checks, the canonical chem-box
asset manifest, and `git diff --check` passed. Test inventories remained
deterministically generated in temporary run directories, production meshes
and partitions remained external read-only inputs, and no generated inventory
or run output was staged. This completes every Phase 7 gate. The required
phase checkpoint was pushed to `develop_emissions`, and the remote ref resolved
to the exact recorded SHA before this audit entry was finalized.

## Phase 8 — verified emissions visualization and extended throughput

- Date: 2026-08-06
- Branch: `develop_emissions`
- Implementation checkpoint: `50086b0597f33ba6c84092885f57577f57427ea4`
- Remote verification: `origin/develop_emissions` resolved to the checkpoint
  SHA immediately after push
- Clean MUSICA build log: `/tmp/chempas-miem-plots-musica-build.log`
- Evidence run root: `/tmp/chempas-miem-plots.84EB4g`
- Figure manifest:
  `docs/chempas/results/miem-emissions-figure-manifest.json`
- Figure-manifest SHA-256:
  `8f9ba803d44507d39564ed48d316240a79ee9ea99a1a71f830738eb4739a31c4`

Eight-rank evidence runs:

| Figure role | Scenario | Simulated evidence | Passing report SHA-256 |
|---|---|---|---|
| Spatial | R3 `cell_time_signature/exact_start` | 3 seconds; final exact-grid interval-start frame | `e22d8912c1996c142fc73f55b5f6c52ade820406e53bffd218961f095715215e` |
| Layered | R6 `layered_diagnostics/default` | 3 seconds; final 25%/75% elevated profile and bounded groups | `c60ff73ac7add837ebee55101e91f5bee6e442303f9b1100166aff804db82657` |
| Budget | R2 `constant_flux/default` | 1,800 seconds; 600 chemistry intervals; all 31 frames | `886b3e999d9686ee5004c5b78218c8567c6ec08d10962b5e63529f8679563a7e` |

The plotting script requires all three reports to use the expected scenario,
variant, fixture, schema, and eight-rank configuration; every scenario-specific
throughput assertion must pass, and each report's history SHA-256 must match the
plotted NetCDF file. It separately verifies initial-zero and finite nonnegative
diagnostics, exact mesh/history global-ID order, physical units, layered and
group closure, and the R2 diagnostic-integral/tracer mass history. The manifest
then records the three reports, three histories, grid input, selected frames,
run configurations, validation results, and every PNG/PDF hash and size.

The extended R2 run emitted `0.022447378466092408 kg` of NO and
`0.0024941531628992096 kg` of NO2 by the analytical source integral. The final
independently reconstructed diagnostic/tracer relative errors were
`3.863977877410389e-15` and `4.329587211638343e-14`, respectively. R6 layer,
sector, and category maximum absolute closure error was exactly zero for both
species. Repeated plot generation from the same evidence produced byte-identical
PNG, PDF, and manifest files.

Verification performed:

- Clean GNU 15.2 double-precision, MPI-enabled, MUSICA-enabled atmosphere
  build: pass; MUSICA-Fortran 0.16.5 was present in the final link.
- R3, R6, and extended R2 full MPAS throughput gates on 8 ranks: pass.
- Focused plot and documentation contracts: 11 tests passed.
- Complete Python discovery: all 42 tests passed.
- Python compilation, shell syntax, canonical chem-box asset verification, and
  `git diff --check`: pass.
- Visual inspection of all three 300-dpi PNGs: pass for units, labels, color
  contrast, clipping, titles, legends, and closure annotations.
- The pinned model environment does not include Sphinx, so an optional HTML
  render was not available; machine-checked local links and every figure hash
  passed instead.

The synthetic inventories and NetCDF histories remain in the temporary
evidence root and are not checkpoint content. The committed artifacts are the
plotter, tests, documentation, six small figure files, and provenance manifest.
A longer synthetic R3 or R6 run was rejected as redundant. The next longer
science run is gated on a science-grade exact-grid inventory: first a one-hour
production-grid throughput shakedown, then at least a full diurnal cycle with
reactive/source budget expectations appropriate to the selected mechanism.

## Phase 9 — global coupled MIEM validation and release evidence

- Date: 2026-08-06
- Branch: `develop_emissions`
- Evidence-base checkpoint: `4ffc5da925388f9e83a2a04f2531ba24cc46aed8`
- Evidence-base remote verification: `origin/develop_emissions` resolved to the
  evidence-base checkpoint before the Stage 9E release audit
- Required release checkpoint: `feat: complete global coupled MIEM validation`
- Release checkpoint: `2b172b03f16337b5c84f6812c16c9cd8e04649fe`
- Release remote verification: immediately after push,
  `origin/develop_emissions` resolved to the exact release checkpoint SHA
- Release manifest:
  `docs/chempas/musica/global-runs/stage9e-release-manifest.json`
- Release-manifest SHA-256:
  `6ab90faf9b3547bd80d2b9432ef408c7878d6f40190be4e155b7b521309928ad`
- Candidate executable SHA-256:
  `ff7166f119c407a18108ce7b6171f7a53a44ef3e6cfc75f6f31550d6a3d131c2`

The clean-staging G3 reproduction used only tracked orchestration plus
external-manifest-resolved inputs and passed all 20 assertions. Its report
SHA-256 is
`d079a9e099811d0ad1e004bcde54665a3a46dd667ecea2b898e0ee4a93ea4010`.
The decisive recheck of the retained 24-hour continuous, 12+12-hour restart,
and matched no-MIEM control trajectories passed all 47 A1 assertions. Its
report SHA-256 is
`9e6d8a9514faa206bef5a7889cec6b488d7d144717ffcdf00f41f047c76ec9a5`;
after removing only `.telemetry.available_disk_bytes_after_run`, it is
canonically identical to the accepted Stage 9D report. The portable figure
manifest remains
`cbab4d96e0b30dbf3088a56643281f30d247e05ac125394f6c9e9273f742ee78`.

All nine R0-R6 reports passed, including surface, time interpolation,
restart/substeps, lightning coexistence, vertical profiles, and bounded group
diagnostics. The selected/full and one/eight-rank mapping contract passed at
five inventory samples; all six intended runtime failure paths failed with the
required messages. Strict E0 passed for supercell ABBA, global Chapman-NOx, and
supercell lightning against pre-emissions CheMPAS-A source `4eb4e677...`
built with the candidate MUSICA `1403e3d...` and MIEM `9fdf14a...` revisions.
The immutable original Phase 0 manifest is retained separately, and all 195
canonical scientific fields match the current-stack recapture exactly.

External retained roots include the G3 staging tree, A1 acceptance tree,
R0-R6 regression tree, preimplementation build, baseline capture and immutable
baseline root, strict E0 comparisons, and final contract logs. The release
manifest records their logical paths and sizes under
`CHEMPAS_EMISSIONS_DATA_ROOT`; no automatic cleanup is configured, and no
large inventory, history, restart, or baseline NetCDF file is tracked. The six
inspected Phase 9 PNG/PDF files, both manifests, compact reports, regression
logs, and baseline records were also byte-verified in
`~/Desktop/CheMPAS-A-Phase9-global-emissions` for review.

Final pre-checkpoint verification passed:

- complete Python discovery: all 97 tests passed;
- Python compilation and relevant shell syntax: pass;
- canonical chem-box mesh/init/partition manifest: pass;
- every Stage 9E JSON document and `git diff --check`: pass; and
- GNU Fortran 15.2 MUSICA/MIEM revision, ABI, static dependency order, and
  MICM-plus-emissions constructor link probe using only pkg-config flags: pass.

This evidence validates the exact-grid reader, applied NO/NO2 throughput,
coupled dynamics/transport/reactive chemistry, source and NOy budgets,
restart/control behavior, bounded diagnostics, performance telemetry, and
reproducible staging. The inventory and date-matched meteorology are suitable
for this coupled-process acceptance run. The idealized, unspun Chapman-NOx
background means its first-day concentrations remain non-production
air-quality results.
