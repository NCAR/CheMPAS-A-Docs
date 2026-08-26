# MVP Stage 5: Full Regression

Stage 5 passed on candidate commit
`a2ae24da87d74ae19a615363ba793b6268f3c253`. A clean tracked worktree was
built, the complete Python suite passed, and every one of the 16 tracked shell
contract suites passed against that exact source tree. The compact record is
[`stage5-full-regression-audit.json`](stage5-full-regression-audit.json).

## Clean Build

The tested Git tree was
`7f8663cb487090aa8f25496c770a758c9e0c4cfe`. The double-precision,
MUSICA-enabled `gfortran` build completed in 100.02 seconds after the build
environment preflight passed. The resulting 14,165,560-byte
`atmosphere_model` had SHA-256
`0049e8968273f95ec7404a4c123fa514458b29681fd2c8f117634b78d4d0988a`,
identical to the executable promoted through the global ladder.

The pinned closure was:

- GNU Fortran 15.2.0 and Open MPI 5.0.10;
- Python 3.14.6;
- MUSICA-Fortran 0.16.5 at
  `1403e3d22717bc87f3bf9d0aa591caf039c92bbc`;
- MIEM at `9fdf14a189262eecb677862d877ab72b06c95e21`; and
- netCDF4 1.7.4, NumPy 2.5.1, Matplotlib 3.11.0, SciPy 1.18.0, and
  PyYAML 6.0.3.

The compiler emitted only known reorder and unused-parameter warnings from
the pinned MICM headers. There were no CheMPAS-A build errors or test waivers.

## Repository Test Results

`python -m unittest discover -v` passed all 268 tests in 27.660 seconds
(28.42 seconds wall time). Python byte compilation also passed. Static
validation parsed all 114 tracked JSON files and 43 tracked YAML files,
validated every declared JSON Schema as Draft 2020-12, checked Bash syntax for
all 22 tracked shell scripts, and passed `git diff --check`.

Every tracked `scripts/test_*.sh` contract passed:

| Contract | Wall Time | Evidence |
|---|---:|---|
| `test_global_tropo_f0.sh` | 5 s | Expanded box, column, photolysis, NOy, radical, and Troe contracts |
| `test_global_tropo_troe.sh` | 2 s | Three 16-point JPL/MICM Troe matrices |
| `test_mvp_co_source.sh` | 3 s | Exact-zero and analytic Tier C CO source, mass, and carbon input |
| `test_mvp_tier_c_sources.sh` | 2 s | Tier C photolysis, NO/NO2/CO sources, and source ledgers |
| `test_mozart35_box.sh` | 19 s | Independent 48-hour SciPy/MICM comparison |
| `test_mozart35_tuvx.sh` | 1 s | Eighteen one-to-one photolysis channels |
| `test_musica_emission_contracts.sh` | 2 s | MICM source binding, cache, methane exchange, and mechanism contracts |
| `test_musica_multiple_inventories.sh` | 1 s | Independent NOx and CH4 inventory summation |
| `test_miem_net_flux.sh` | 2 s | Signed methane exchange and applied mass |
| `test_miem_mpi_mapping.sh` | 20 s | One/eight-rank and selected/full-grid identity |
| `test_mvp_multiple_inventories.sh` | 1 s | Independent CAMS and FINN interpolation and sum |
| `test_mvp_prescribed_fields.sh` | 3 s | One/eight-rank prescribed-field and TUV-x adapter contracts |
| `test_miem_failure_paths.sh` | 14 s | All six expected fail-closed runtime cases |
| `test_miem_disabled_baselines.sh` | 436 s | Three chemistry/MIEM-disabled cases bitwise identical |
| `test_mvp_local_integration.sh` | 5 s | Eight-rank normal/strict synthetic MVP integration |
| `test_miem_integration.sh` | 46 s | R0--R6 runtime, restart, mapping, and diagnostics matrix |

The rounded shell-contract wall time was 562 seconds. The
MIEM-disabled E0 gate established bitwise identity for supercell ABBA, global
Chapman-NOx, and supercell lightning. Together with the prescribed-field and
mapping contracts, the suite contains representative one-rank and eight-rank
executable coverage.

## Historical Static-Profile Migration

The first full-suite attempt exposed a real compatibility gap in the retained
Chapman-NOx E0 fixture: its historical namelist predates the explicit
`config_tuvx_upper_column_mode` selector. Runtime validation correctly refused
the ambiguous combination of extension inputs and mode `none`.

Commit `a2ae24da` fixed the test harness without weakening runtime validation.
It converts only the staged copy of a qualifying historical static-profile
namelist to explicit `legacy_static`, and records both the original and staged
configuration hashes in the E0 report. Two focused unit tests cover the
migration and its refusal conditions. The complete suite was then rerun at the
fixed exact tip; all three E0 cases were bitwise identical to their frozen
scientific baselines.

## Reproduction

From a detached, clean worktree at the tested commit:

```bash
conda activate mpas
scripts/check_build_env.sh
eval "$(scripts/check_build_env.sh --export)"

make -j8 gfortran \
  CORE=atmosphere PIO="$PIO" NETCDF="$NETCDF" PNETCDF="$PNETCDF" \
  PRECISION=double MUSICA=true

python -m unittest discover -v
python -m compileall -q scripts tests
```

Set the two external roots, then run every shell contract. The two commands
with special inputs are shown explicitly; the remaining scripts use their
default exact-tip build artifacts.

```bash
export CHEMPAS_EMISSIONS_DATA_ROOT=/path/to/emissions-science
export CHEMPAS_TUVX_DATA=/path/to/MUSICA/configs/tuvx/data

scripts/test_mvp_multiple_inventories.sh \
  "$CHEMPAS_EMISSIONS_DATA_ROOT"
scripts/test_miem_disabled_baselines.sh . --case all

for test_script in scripts/test_*.sh; do
  case "$test_script" in
    scripts/test_mvp_multiple_inventories.sh|scripts/test_miem_disabled_baselines.sh)
      ;;
    *) "$test_script" ;;
  esac
done
```

Hash-recorded logs remain outside Git at
`reports/mvp-regression/a2ae24da` beneath `CHEMPAS_EMISSIONS_DATA_ROOT`.
