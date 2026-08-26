# Stage 9A inventory qualification

**Gate result:** PASS on 2026-08-06. The first Phase 9 inventory is
CAMS-GLOB-ANT v6.2 monthly anthropogenic NOx. The provider's July and August
2024 frames bracket the planned 2024-07-01 00:00 UTC to 2024-07-02 00:00 UTC
acceptance period.

## Scientific identity and use

- Product: CAMS-GLOB-ANT v6.2, global 0.1 degree by 0.1 degree monthly
  anthropogenic emissions, distributed through ECCAD-AERIS.
- Dataset DOI: [10.24380/eets-qd81](https://doi.org/10.24380/eets-qd81).
  The peer-reviewed [CAMS-GLOB-ANT data description](https://doi.org/10.5194/essd-16-2261-2024)
  documents the product family and v5.3 release; the exact v6.2 identity is
  pinned separately by the provider path and `product_version` NetCDF
  attribute.
- License: CC BY 4.0. The selected provider OPeNDAP hyperslab has no published
  checksum. CheMPAS-A's normalized local subset is therefore pinned by byte
  size 95,931,202 and SHA-256
  `2687ea4f95161119f3e7962f65a1026898a6c3730d509001ef30190fdd83b032`.
- Selection: full global grid; times 294 and 295 (2024-07-01 and 2024-08-01);
  sectors `agl`, `ags`, `awb`, `com`, `ene`, `fef`, `ind`, `ref`, `res`,
  `shp`, `swd`, `tnr`, and `tro`; plus the provider `sum` field.
- Retention: the raw subset is external at
  `$CHEMPAS_EMISSIONS_DATA_ROOT/raw/cams-glob-ant-v6.2/`. Git contains only
  the manifest, software, audit, and documentation.

## Chemical mapping

CAMS reports NOx mass flux as nitric-oxide-equivalent mass with molecular
weight 30 g mol-1. HERMESv3 documents a mass-based 90% NO / 10% NO2 profile
for non-road sectors ([Guevara et al., 2020](https://doi.org/10.5194/gmd-13-873-2020)).
Directly multiplying an NO-equivalent flux by 0.9 and 0.1 would lose elemental
nitrogen because NO and NO2 have different molecular weights. For native flux
`F`, mass fractions `w`, and species molecular weights `M`, preprocessing uses

```text
F_explicit = F / M_NO / (w_NO / M_NO + w_NO2 / M_NO2)
F_NO       = w_NO  * F_explicit = 0.9324324324324323 * F
F_NO2      = w_NO2 * F_explicit = 0.1036036036036036 * F
```

Thus `F_NO / M_NO + F_NO2 / M_NO2 = F / M_NO` exactly. The explicit-species
mass is larger than the NO-equivalent reporting mass; that is a basis
conversion, not created nitrogen.

| Source time | Native NO-equivalent | Explicit NO | Explicit NO2 | Native/explicit N closure |
|---|---:|---:|---:|---:|
| 2024-07-01 | 2352.789383 kg s-1 | 2193.817128 kg s-1 | 243.757459 kg s-1 | exact in float64 |
| 2024-08-01 | 2325.593657 kg s-1 | 2168.458951 kg s-1 | 240.939883 kg s-1 | `1.88e-16` relative |

The 90/10 mapping is a declared emissions-model assumption, not native CAMS
NO and NO2 data. The first global run applies it uniformly because the global
inventory does not contain vehicle/fuel detail for the fleet-dependent road
factors recommended by HERMESv3. Results sensitive to primary NO2 require a
separate road-speciation sensitivity experiment.

## Data-quality audit

The machine-readable
[`stage9a-inventory-audit.json`](stage9a-inventory-audit.json) integrates
native fields on exact spherical 0.1-degree cell areas using the MPAS sphere
radius of 6,371,229 m. It passed all of these assertions:

- every selected value is present, finite, and nonnegative; neither missing
  values nor negative corrections are converted to zero;
- the native grid covers the sphere to `2.33e-15` relative area error;
- the provider aggregate reconstructs from all retained sectors to
  `3.69e-10` relative in July and `2.17e-10` in August;
- July/August totals are 74.25/73.39 Tg NO-equivalent yr-1 and
  34.65/34.25 Tg N yr-1;
- explicit NO/NO2 conversion preserves elemental-N molar flux to float64
  precision.

Both land and ocean cells are retained. Individual point facilities and stack
parameters cannot be recovered from the provider-gridded fields. The monthly
inventory has no weekly or diurnal activity cycle. Stage 9B assigns tracked
sector profiles but cannot reproduce meteorology-dependent plume rise. These
limitations, and the lack of chemical spin-up in a first-day run, prohibit
interpreting the acceptance trajectory as production-ready concentrations.
