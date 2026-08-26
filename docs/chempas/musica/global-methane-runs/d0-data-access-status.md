# CAMS Methane D0 Data-Access Status

Checked 2026-08-15 at 18:37 UTC.

The source-selection gate passes. The current CAMS ADS catalogue still exposes
the exact frozen `v24r2` surface-plus-satellite solution for all three required
requests: three-dimensional methane concentration, column-mean methane, and
posterior total/component surface exchange. The content-addressed form and
constraint documents still match the pinned hashes.

The data-acquisition gate cannot run on this machine because neither supported
credential source is present:

- `ADS_API_TOKEN` is absent;
- `~/.cdsapirc` is absent; and
- no secret value was read or recorded.

The supported `cdsapi` 0.7.7 client is installed and declared in
`environment.yml`. A real acquisition attempt stopped with exit code 2 before
submitting any request and before creating a partial data artifact:

```text
ADS authentication is unavailable; set ADS_API_TOKEN or configure ~/.cdsapirc
```

This is a hard stop, not permission to substitute another CAMS release or to
fabricate a concentration, posterior exchange field, global run, or science
plot. CAMS-GLOB-ANT v6.2 anthropogenic CH4 and the NOAA July 2024 benchmark are
already acquired and audited, but they cannot replace the missing inversion
background and posterior product.

Once an authorized ADS credential is available and the dataset terms are
accepted for that account, rerun:

```bash
conda run -n mpas python scripts/acquire_cams_methane_inversion.py acquire \
  --requests test_cases/global_methane/cams-inversion-v24r2-requests.json \
  --report "$CHEMPAS_EMISSIONS_DATA_ROOT/cams/inversion/v24r2/acquisition.json" \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT"
```

Then complete the posterior remap, CAMS initial state, C/Z promotion ladders,
visual inspection, and evidence publication described in
[`GLOBAL_TROPOSPHERIC_METHANE.md`](../GLOBAL_TROPOSPHERIC_METHANE.md). The
machine-readable status is
[`d0-data-access-status.json`](d0-data-access-status.json).
