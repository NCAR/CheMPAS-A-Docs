# Global Tropospheric Methane Stage 0 Baseline

**Recorded:** 2026-08-15 (America/Denver)
**Result:** PASS

This report freezes the pre-methane baseline required by
`docs/chempas/mvp/PLAN_GLOBAL_TROPOSPHERIC_METHANE.md`. The tests and build below were run before
any methane implementation file was changed. Existing accepted global NOx
evidence under `docs/chempas/musica/global-tropo-runs/` was read only.

## Source Baseline

| Item | Frozen value |
|---|---|
| Branch point | `8b003fbd221cfabdff69c553a647a9bf08fbe16b` |
| Branch-point subject | `Merge branch 'develop_emissions' into develop` |
| Working branch | `develop_tropo_methane` |
| Compiler | GNU Fortran 15.2.0 (conda-forge gcc 15.2.0-19) |
| MPI | Open MPI 5.0.10 |
| NetCDF-C | 4.10.1 |
| NetCDF-Fortran | 4.6.3 |
| Python | 3.14.6 |
| Precision | double |
| MUSICA support | enabled |

The fresh build used these explicitly pinned chemistry dependencies:

| Dependency | Revision |
|---|---|
| MUSICA | `1403e3d22717bc87f3bf9d0aa591caf039c92bbc` |
| MICM | `bb57684a2047f0e58f30b199366294af879e8597` |
| MIEM | `9fdf14a189262eecb677862d877ab72b06c95e21` |
| MechanismConfiguration | `82c159ae6d74934318ffd6c405a45c2159065b12` |
| TUV-x | `bbf7dd9a144fa0f0294b3779f3f993818638e20c` |

Canonical external data are addressed below
`${CHEMPAS_EMISSIONS_DATA_ROOT}`; source and build locations are represented in
portable evidence as `${CHEMPAS_REPOSITORY_ROOT}` and
`${CHEMPAS_F0_BUILD_ROOT}`. No machine-specific absolute data-root path is
embedded in a tracked science receipt.

## Accepted Inputs Held Immutable

| Artifact | SHA-256 |
|---|---|
| Exact-grid CAMS-GLOB-ANT v6.2 NO/NO2 inventory | `d213866000e8a633954d0c730ba5524f729f26a97d02cc5a13d8b405aa6c8e9c` |
| Expanded tropospheric initial state | `7ccb0670cb49374de78187761cf410690a4b8fc4d4a27533a5ba97deed907e78` |
| x1.40962 graph | `95f28fdbb0f10d2bef72c9f387e73c7a3a92184b32a094cfbfa3bc00f9f4c836` |
| Eight-rank partition | `f56e75e1f408b632fd5cd22ad05cc59fdbb54daf1e2f8f3d6298147a1e7f577b` |

The accepted NOx executable and the fresh baseline executable have the same
SHA-256:
`ff7166f119c407a18108ce7b6171f7a53a44ef3e6cfc75f6f31550d6a3d131c2`.
The fresh executable is 14,082,536 bytes.

## Verification Inventory

### Static and unit tests

```text
python -m compileall -q scripts tests
for script in scripts/*.sh; do bash -n "$script"; done
python -m unittest discover -v
```

Results:

- Python byte compilation: PASS.
- Shell syntax: PASS for every tracked `scripts/*.sh` entry.
- Canonical Python suite: PASS, 152 tests in 4.013 seconds.

The suite count is recorded here as baseline evidence rather than enforced as
a constant in a test driver; later additions are therefore not mistaken for a
regression.

### Mechanism reproducers

```text
scripts/test_global_tropo_troe.sh
scripts/test_musica_emission_contracts.sh /tmp/chempas-methane-baseline.Vdilxc
```

Results:

- Both accepted global tropospheric configurations passed the 16-point JPL
  Troe matrix.
- All four MUSICA/MIEM emission-contract configurations passed.

### Fresh isolated release build

The source was exported from the exact branch-point commit into
`/tmp/chempas-methane-baseline.Vdilxc`, so untracked working-tree files could
not affect the build. The effective build command was:

```text
make -j8 gfortran CORE=atmosphere OPENMP=false AUTOCLEAN=true \
  PRECISION=double MUSICA=true
```

The environment selected the conda MPAS compiler/MPI/NetCDF stack, PnetCDF
from the same prefix, PIO under `/home/fillmore/software`, and the pinned
MUSICA prefix listed above. The build preflight passed. Elapsed wall time from
build-directory creation to executable timestamp was approximately 134
seconds.

## Promotion Decision

Stage 0 passes. The current unit/static suite, mechanism reproducers, MIEM
contracts, and a clean release build all succeed. The accepted NOx reports and
figures were not regenerated or modified, and their executable hash is exactly
reproduced by the isolated baseline build.
