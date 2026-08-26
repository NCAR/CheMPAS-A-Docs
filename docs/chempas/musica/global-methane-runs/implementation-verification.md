# Global Methane Implementation Verification

Verified 2026-08-15 through 19:36 UTC on `develop_tropo_methane`, relative to
the accepted `develop` baseline
`8b003fbd221cfabdff69c553a647a9bf08fbe16b`. The containing Git commit is the
implementation revision; embedding that commit's hash in this file would be
self-referential.

## Result

The software, mechanism, coupling, harness, checker, plotting, and publication
paths pass their complete local qualification. Actual global methane science
promotion remains stopped at D0 because the CAMS inversion concentration,
XCH4, and posterior surface-exchange files cannot be retrieved without an ADS
credential. No global C/Z result, science figure, or Desktop plot bundle is
claimed.

## Build

The final source tree received a clean double-precision MUSICA release build:

```bash
conda run -n mpas env \
  OMPI_CC=gcc OMPI_CXX=g++ OMPI_FC=gfortran \
  NETCDF=/home/fillmore/miniforge3/envs/mpas \
  NETCDFF=/home/fillmore/miniforge3/envs/mpas \
  PNETCDF=/home/fillmore/miniforge3/envs/mpas \
  PIO=/home/fillmore/software \
  PKG_CONFIG_PATH=/home/fillmore/software/musica-1403e3d22717bc87f3bf9d0aa591caf039c92bbc/lib/pkgconfig \
  make -j8 gfortran CORE=atmosphere OPENMP=false AUTOCLEAN=true \
  PRECISION=double MUSICA=true
```

The build passed. `atmosphere_model` is 14,100,160 bytes with SHA-256
`e95e93b15c0a1f5ca71dbbc32f070a9c0f0d734b1aadefa89ea44a0b4c2905db`.

The qualified environment is Python 3.14.6, GNU Fortran 15.2.0, and Open MPI
5.0.10. `scripts/check_build_env.sh` passed its compiler, ABI, static-link, and
MICM-plus-emissions constructor probes. It resolved MUSICA revision
`1403e3d22717bc87f3bf9d0aa591caf039c92bbc` and MIEM revision
`9fdf14a189262eecb677862d877ab72b06c95e21`.

## Test Matrix

`conda run -n mpas python -m unittest discover -v` passed all 230 tests in
28.319 seconds. Python byte-compilation, shell syntax checks, strict JSON
parsing, and
`git diff --check` also passed.

Every canonical shell/compiled contract passed against the final executable:

| Contract | Qualified behavior |
|---|---|
| `test_global_tropo_f0.sh` | expanded box, column, photolysis, NOy, radical, and Troe contracts |
| `test_global_tropo_troe.sh` | all three pinned mechanisms match the 16-point independent JPL matrix |
| `test_musica_emission_contracts.sh` | existing emission cache, Tier C CH4, signed uptake, and MOZART-35 host/tracer contracts |
| `test_musica_multiple_inventories.sh` | independent NOx and CH4 inventories and signed posterior configuration |
| `test_miem_net_flux.sh` | signed CH4 source and uptake, vertical application, and net mass closure |
| `test_mozart35_tuvx.sh` | all 18 photolysis channels load one-to-one |
| `test_miem_mpi_mapping.sh` | selected/full-grid and one-/eight-rank mappings are identical at five samples |
| `test_mozart35_box.sh` | actual MICM and independent SciPy agree for 48 hours |
| `test_miem_integration.sh` | complete R0-R6 runtime matrix, interpolation, restart, lightning coexistence, layers, and MPI identity |
| `test_miem_failure_paths.sh` | all six declared eight-rank runtime failures stop as required |
| `test_miem_disabled_baselines.sh` | supercell ABBA, global Chapman-NOx, and supercell lightning scientific fields remain bitwise identical |

The tracked 48-hour box report is
[`mozart35-box-qualification.json`](mozart35-box-qualification.json). All six
of its convergence, finite/nonnegative, state-parity, major-species/ledger,
and C/N/S conservation assertions pass. The report SHA-256 is
`05a8ee8fe51f3872407fef9d287022bbf732ba845d10c4031c076bea8cab676b`.

## Input Boundary

The current ADS catalogue audit passes for the exact frozen CAMS v24r2
surface-plus-satellite selection. The acquisition command then stops before
request submission because both supported credential sources are absent. The
machine-readable and human-readable evidence is in
[`d0-data-access-status.json`](d0-data-access-status.json) and
[`d0-data-access-status.md`](d0-data-access-status.md).

The accepted 40,962-cell, 26-level legacy Tier C state was expanded into the
real Tier Z contract. The expansion preserves all 152 source variables and
qCH4 bitwise, adds the required MOZART-35 fields, initializes the five ledgers
to zero, and declares `legacy_background` rather than CAMS lineage. Both the
runtime-manifest builder and gate runner reopen initial states and reject a
Tier/background lineage mismatch before staging. The runner records the
validated global-attribute contract in its run and stage metadata.

The already available compact input evidence remains hash-closed:

| Evidence | SHA-256 |
|---|---|
| CAMS inversion v24r2 source selection | `03f6df61e7fbb25c35ade29bbf3822e7e5616a94fd0c944c59c5f78d4e13c4b6` |
| CAMS-GLOB-ANT v6.2 CH4 acquisition audit | `bdbee955149dfa4a7871a4268b5943e095aab993a69544da42de2fdffe472ed4` |
| CAMS-GLOB-ANT v6.2 CH4 remap audit | `4ffb026f2b125c14aec354d98a00667284928c3adb7c1a2e5ac847cb25e675ea` |
| NOAA July 2024 CH4 benchmark audit | `8b28259b0bb115bf5c9bf7d451e6c1092d5f9caea4c5e6cfd8ceea89c0e67352` |
| D0 access status | `350234bbc2c7b580040c5139de4799f3d1b0008e274e92102dae1becde9dd83e` |
| Runtime readiness snapshot | `4e7a4892a27ece87af3383afcde91424fbedf233270020d17463db01fbad69a5` |
| Tier Z legacy initial-state audit | `6d6c3f7a1017878e823a4af37460b4bbfaa6e7976d707f3e52cc4dc14f03f863` |

At the readiness snapshot, the data root had 29,737,672,704 bytes free. The
largest required seven-day Tier Z gate needs 251,846,983,680 bytes under the
frozen guard, and retaining the complete required ladder through publication
needs 921,808,404,480 bytes. These forecasts are recomputed from
`scenarios.yaml` by a unit test rather than entered as unverified prose.

Large provider data, remap weights, model states, histories, restarts, and
plots remain outside Git. The plot publisher will create the Desktop bundle
only after all 14 global reports pass, all six paired figure bundles are
rendered from hash-verified histories, and every PNG receives an explicit
visual-inspection attestation.
