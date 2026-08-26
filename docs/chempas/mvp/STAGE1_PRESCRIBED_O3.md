# MVP Stage 1: Prescribed Upper-Atmosphere O3

Stage 1 passed on implementation commit `8c38297c5906d3fd615d004766bcd39e274b603e`.
The compact machine-readable result is
[`stage1-prescribed-o3-audit.json`](stage1-prescribed-o3-audit.json).

## Delivered Interface

The new consumer-neutral prescribed-field provider validates one exact-grid
NetCDF package, maps global cell IDs to rank-owned cells, and retains only the
two monthly O3 slabs needed by the current Gregorian interpolation bracket.
TUV-x has three explicit modes: `none`, `legacy_static`, and
`spatial_climatology`. The spatial mode uses prognostic MPAS O3 through the
model top and prescribed layer-mean O3 strictly above it; it never writes to
`qO3` and never falls back to the legacy CSV after an error.

The runtime file is prepared offline from the frozen MERRA-2 subset using
first-order conservative ESMF weights. O3 pressure-layer molecular columns are
remapped horizontally, redistributed vertically by geometric overlap onto the
45--100 km grid, and completed outside MERRA-2 support with the frozen
log-linear AFGL reference O3. US Standard Atmosphere 1976 provides the static
temperature and air structure. The exact package SHA-256 is
`a6ecbb5b57fc72485d76ed8cb652666f58c26535bc1f3dbf443b9bc615938301`.

## Verification

The implementation was built with the pinned MUSICA closure and checked with:

```bash
conda run --no-capture-output -n mpas bash -lc \
  'eval "$(scripts/check_build_env.sh --export)"; \
   make -j8 "$CHEMPAS_MAKE_TARGET" CORE=atmosphere OPENMP=false \
   PRECISION=double MUSICA=true'

conda run --no-capture-output -n mpas \
  python -m unittest tests.test_mvp_o3_climatology -v

conda run --no-capture-output -n mpas scripts/test_mvp_prescribed_fields.sh
conda run --no-capture-output -n mpas scripts/test_mozart35_tuvx.sh
```

The one- and eight-rank provider tests independently cover cell selection,
December--January wrapping, leap years and Gregorian century rules, restart
identity, the 0.5 m model-top seam, stored column closure, spatial photolysis
sensitivity, uniform equivalence with the static CSV, the no-extension path,
and unchanged prognostic O3. Corrupt calendar, unit, mesh, vertical-coordinate,
and monthly-column fixtures all fail before use.

The offline science audit found no unmapped source or destination cells. The
largest horizontal O3 column error was `3.14e-16`, the largest vertical
MERRA-2 column error was `7.60e-16`, and the largest stored density/column
error was `1.17e-16`; all are well inside the frozen tolerances.

## Reproduction

With `CHEMPAS_EMISSIONS_DATA` set to the audited external data root:

```bash
python scripts/prepare_mvp_o3_climatology.py verify \
  --package "$CHEMPAS_EMISSIONS_DATA/prescribed/merra2-o3-v5.12.4-x1.40962/merra2-o3-monthly-climatology.x1.40962.nc" \
  --mesh "$CHEMPAS_EMISSIONS_DATA/raw/mpas-x1.40962/x1.40962.static.nc"
```

The full weight-generation and preparation inputs, hashes, methods, and
tolerances are frozen in
[`STAGE0_DATA_CONTRACT.md`](STAGE0_DATA_CONTRACT.md) and
[`prescribed-field-contract.json`](../../_downloads/mvp/prescribed-field-contract.json).
