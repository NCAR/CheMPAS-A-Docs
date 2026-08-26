# Stage 9B science-inventory qualification

Status: **accepted for global coupled shakedowns**. This is a preprocessing and
software-coupling qualification, not a claim that first-day modeled
concentrations are observationally or production ready.

## Qualified chain

- Source: CAMS-GLOB-ANT v6.2 monthly anthropogenic NOx for July and August
  2024, 13 retained sectors, native 0.1-degree global grid.
- Destination: official MPAS x1.40962 static mesh, 40,962 cells,
  `chempas-mesh-sha256-v1`
  `cdd75b787f487302df17b31c2dd7aaf7082a7cb265a711792ef0e5f3ceebda12`.
- Remapper: ESMF 8.9.1 first-order conservative, `dstarea` normalization,
  canonical user areas, explicit all-active source and destination masks.
- Chemistry mapping: native NOx expressed as NO is transformed to explicit NO
  and NO2 with the documented nitrogen-conserving 90/10 mass profile. The MIEM
  configuration therefore uses unit scaling and does not speciate a second
  time.
- Runtime boundary: `regridding: none`; all 13 sectors inject into the surface
  model layer and use distinct additive MIEM categories.

All large inputs and products are external under
`CHEMPAS_EMISSIONS_DATA_ROOT`. The versioned external-input manifest records
their logical paths, licenses, byte sizes, and SHA-256 values.

## Conservation and exact-grid review

- All 6,480,000 source and 40,962 destination cells are represented by
  7,773,510 sparse weights; there are no unmapped cells.
- Maximum physical source-area reconstruction error is
  `2.0230e-12`, below the declared `2.0e-7` tolerance. The largest local
  constant-field row-sum difference is `1.1360e-5`; it is reported separately
  and is below the `1.0e-3` qualification bound.
- Native-to-remapped integrated mass differences are at most
  `1.20e-15` among individual sectors and `3.91e-16` for the provider
  aggregate. Provider aggregate versus retained-sector closure is
  `3.69e-10` in July and `2.17e-10` in August.
- July explicit global rates are 2,193.8171 kg s-1 NO and 243.7575 kg s-1
  NO2 (69.2316 and 7.6924 Tg yr-1). Elemental-N speciation closure is
  `1.86e-16`; August closure is exact at reported precision.
- The packaged NetCDF has 28 nonnegative finite fields: 26 mapped
  species/sector fields and two diagnostic aggregate fields. Ascending global
  IDs, coordinates, areas, units, Gregorian brackets, and the stored mesh
  fingerprint all match the official static mesh.
- The G0-G4 model init retains the finite 26-level JW prognostic state but
  replaces all 79 compatible time-independent fields with the official static
  values. Its mesh fingerprint is exact, and the packaged inventory validates
  against the actual resulting model init. This alignment is explicitly
  prohibited as the Stage 9D meteorological science state.

## Public-API and visual review

The public MUSICA/MIEM Fortran harness ran on the verified eight-rank
partition at 2024-07-01 00:00, July 8 18:00, July 16 12:00, July 24 06:00,
and the exact 2024-08-01 00:00 UTC endpoint. Rank ownership sums to 40,962
cells once. Every full-grid and selected-cell rank stream is byte-identical.
The MIEM values also agree with an independent 13-sector linear interpolation:
the largest absolute NO difference is `2.07e-25 kg m-2 s-1`, with a declared
`1.0e-24 kg m-2 s-1` roundoff floor for effectively zero cells.

The protocol-compliant figure bundle was inspected at full resolution. It
shows physically recognizable land, shipping, and high-activity source
patterns; consistent explicit NO and NO2 spatial structure; road, power,
industry, and shipping dominance in the global sector budget; smooth monthly
interpolation; plausible zonal structure; and the intentionally surface-only
vertical allocation. No missing swaths, seam discontinuity, negative fields,
or unexplained sector/time discontinuity was found.

Review disposition: **pass for G0-G4 and the Phase 9 acceptance experiment**,
subject to the limitations below. The review is a recorded CheMPAS technical
science audit, not independent peer review.

## Limitations carried into the run

- Monthly means omit weekly and diurnal activity profiles.
- The global 90/10 split is an emissions-model assumption; CAMS does not
  provide native explicit NO and NO2 fields or the fleet detail needed for a
  road-specific primary-NO2 fraction.
- All sectors are surface injected. Facility stack metadata and
  meteorology-dependent plume rise are absent.
- Lightning and other online NOx sources remain disabled until MIEM-only
  source closure is established.
- A first-day coupled result is a process-validation experiment, not a
  chemically spun-up concentration product.

Machine-readable evidence:

- `stage9b-weight-audit.json`
- `stage9b-remap-audit.json`
- `stage9b-selected-cell-audit.json`
- `stage9b-shakedown-init-audit.json`
- `stage9b-figure-manifest.json`
