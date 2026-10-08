# TUV-x Photolysis Integration

CheMPAS-A computes photolysis rate constants for its MICM chemistry mechanisms
with TUV-x, the photolysis component of MUSICA. TUV-x runs as an independent
one-dimensional column for each MPAS cell owned by an MPI task, using the
model's own heights, temperature, air density, ozone, and cloud and rain
water, and returns one rate per photolysis reaction per model level.
CheMPAS-A writes those rates into MICM as external rate parameters before the
chemistry solve. When no TUV-x configuration is given, a single-rate
`cos(SZA)` fallback can drive `jNO2` instead.

Photolysis, like the rest of the chemistry coupling, is available only in
builds compiled with `MUSICA=true`. The coupling sequence is described in
[Chapter 8](../../users-guide/08-chemistry-coupling.md) of the User's Guide,
and every `&photolysis` option is listed in section B.14 of
[Appendix B](../../users-guide/0B-model-namelist.md).

## What It Provides

- Clear-sky photolysis computed per column from the host atmospheric
  profiles.
- Cloud attenuation from the MPAS cloud water (`qc`) and rain water (`qr`).
- Solar geometry from the model clock, either domain-wide or per cell.
- Any number of photolysis reactions per mechanism, matched between TUV-x and
  MICM by name.
- An adjustable photolysis update interval.
- An optional column above the MPAS model top, from a static profile or a
  spatial monthly O3 climatology.
- A `cos(SZA)` fallback for mechanisms whose only photolysis reaction is
  `jNO2`.

## Source Files

All paths are under `src/core_atmosphere/chemistry/`.

| File | Role |
|------|------|
| `mpas_tuvx.F` | TUV-x initialization, per-column profile updates, cloud optical depth, rate extraction, extension CSV reader |
| `mpas_solar_geometry.F` | `solar_cos_sza`: cosine of the solar zenith angle from day of year, UTC, latitude, and longitude |
| `mpas_atm_chemistry.F` | Namelist handling, choice between TUV-x and the fallback, host-state extraction, update-interval gating, `j_<rate>` diagnostics |
| `musica/mpas_musica.F` | `musica_cache_photo_indices` and `musica_set_photolysis_rates`: MICM `PHOTO.<name>` lookup and rate write-back |
| `mpas_prescribed_fields.F` | Reader for the spatial monthly O3 climatology package |

## Clear-Sky Photolysis

At chemistry initialization, `tuvx_init` builds the TUV-x solver from the JSON
file named by `config_tuvx_config_file`. CheMPAS-A supplies the height grid,
the air, temperature, O3, and O2 profiles, and a cloud radiator as from-host
objects. The height grid has `nVertLevels` sections, plus the extension layers
when an upper-column mode is active. Wavelength grids, the extraterrestrial
flux, cross sections, quantum yields, surface albedo, and the
radiative-transfer solver come from the JSON file and the TUV-x data files it
references. The shipped configurations use the delta-Eddington solver and a
uniform surface albedo of 0.10.

On each photolysis update, `tuvx_compute_photolysis` runs once per cell:

1. Layer edges come from `zgrid`, converted to km. Extension edges, if any,
   are appended above the model top.
2. Air number density is computed from total pressure and temperature as
   `p / (R T)`. O3 number density is `qO3` times dry-air density, because
   MPAS tracers are dry-air mass mixing ratios. O2 is 0.2095 times the air
   number density.
3. Edge values are averages of adjacent layer midpoints; the bottom and top
   edges take the nearest midpoint value. Layer densities (molecule cm⁻²) are
   number density times layer thickness.
4. Air above the top of the column is represented by an exo-layer density with
   a 7 km scale height, so slant paths in spherical geometry do not treat it
   as vacuum.
5. TUV-x returns rates on layer edges. CheMPAS-A averages adjacent edges to
   give one value per MPAS layer and discards the extension-layer rates.

When `cos(SZA) ≤ 0`, the TUV-x call is skipped and every rate in that column
is set to zero. The Earth–Sun distance passed to TUV-x is fixed at 1 AU.
Roundoff-scale negative `qO3`, `qc`, or `qr` values are clipped to zero in the
copy passed to TUV-x; the prognostic fields are not changed, and the total
number of clipped values is logged at finalization.

TUV-x requires O3: if TUV-x is configured and the active mechanism has no
`qO3` tracer, chemistry initialization stops with an error.

## Cloud Attenuation

CheMPAS-A registers a host-driven cloud radiator, `clouds`, with TUV-x. Its
optical depth in each MPAS layer comes from the cloud water and rain water
mixing ratios:

```
tau = 3 * LWC * dz / (2 * r_eff * rho_water)
```

with `r_eff = 10 µm` for cloud water and `r_eff = 500 µm` for rain, and
`LWC = q * rho_dry` because the MPAS water species are also dry-air mixing
ratios. The layer optical depth is the sum of the two terms, so per unit mass
rain contributes about 50 times less than cloud water. The same optical depth
is applied at every wavelength of the 102-section CAM wavelength grid, with
single-scattering albedo 0.999999 and asymmetry factor 0.85. Extension layers
are cloud-free.

Within a column, a cloud layer reduces photolysis below it and, by reflection,
increases it above it. If the run has no `qc` tracer, TUV-x runs clear-sky; if
it has no `qr` tracer, rain opacity is zero. Both cases are noted in the log
at initialization.

## Solar Geometry

`solar_cos_sza` in `mpas_solar_geometry.F` computes the cosine of the solar
zenith angle from the day of year and UTC time of the model clock, using the
Spencer (1971) expressions for solar declination and the equation of time.
The same `cos(SZA)` drives both TUV-x and the fallback.

### Per-cell solar geometry

By default (`config_chemistry_use_grid_coords = .false.`), every column uses
the single location given by `config_chemistry_latitude` (degrees N) and
`config_chemistry_longitude` (degrees E). This suits idealized cases in which
solar geometry should be uniform across the domain, such as the
Cartesian-plane supercell. For runs on spherical meshes, set
`config_chemistry_use_grid_coords = .true.`; each cell then uses its own
`latCell` and `lonCell`.

## Fallback Photolysis

When `config_tuvx_config_file` is empty and `config_j_no2_max > 0`, CheMPAS-A
drives a single rate, uniform in the vertical:

```
jNO2 = config_j_no2_max * max(0, cos(SZA))
```

The MICM mechanism must then contain a photolysis reaction named `jNO2` (rate
parameter `PHOTO.jNO2`); otherwise chemistry initialization stops. With an
empty TUV-x file and `config_j_no2_max = 0`, no photolysis rate parameter is
driven and the mechanism need not declare `PHOTO.jNO2`. `config_j_no2_max` is
ignored when TUV-x is active.

The fallback provides only `jNO2`. Mechanisms with other photolysis reactions,
such as Chapman and Chapman + NOx, require TUV-x.

## Multi-Photolysis Plumbing

CheMPAS-A couples TUV-x to MICM through a single-name convention: for every
photolysis reaction, the same string is used in four places —

```
<rxn_name>  == TUV-x JSON "name:" field
            == MICM yaml reaction "name:" field
            == runtime diagnostic variable "j_<rxn_name>"
            == MICM rate parameter key "PHOTO.<rxn_name>"
```

At chemistry initialization, `tuvx_init` enumerates every photolysis reaction
the TUV-x configuration registers and caches the names and TUV-x indices. The
chemistry driver passes the same names to `musica_cache_photo_indices`, which
looks up `PHOTO.<name>` in the MICM rate-parameter ordering. A TUV-x reaction
with no matching MICM rate parameter stops initialization. On each update,
`tuvx_compute_photolysis` fills an `(n_rates, nVertLevels)` slab per cell, and
a single call to `musica_set_photolysis_rates` writes the full
`(n_rates, nVertLevels, nCells)` array into the MICM state and, when
`config_chemistry_ref_solve` is enabled, into the reference state.

### Photolysis diagnostics

The `j_<rate>` fields (s⁻¹) are injected into the diagnostic pool at run time
from the active TUV-x configuration's reaction names, or `j_jNO2` alone for
the fallback; they are not Registry variables. To write them to history, list
the exact field names (for example `j_jNO2`) in
`stream_list.atmosphere.output`. They exist only when chemistry with
photolysis is configured, so remove any `j_<rate>` entries when running
without chemistry to avoid stream-manager warnings. The fields are written
after each photolysis update and keep their values between updates.

### Supported mechanisms

The release ships the first two pairs in `micm_configs/`. The global pair is
published with the CheMPAS-A wiki's
[global chemistry and emissions examples](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions)
rather than in the release.

| MICM mechanism | TUV-x configuration | Rates | Purpose | In v2026.08.01 |
|----------------|---------------------|-------|---------|----------------|
| `lnox_o3.yaml` | `tuvx_no2.json` | jNO2 | Tropospheric NO-NO2-O3 cycle, used with the lightning-NOx source | Yes |
| `chapman_nox.yaml` | `tuvx_chapman_nox.json` | jO2, jO3_O, jO3_O1D, jNO2 | Chapman + NOx catalytic O3 destruction | Yes |
| `global_cams_tropo_ch4nox.yaml` | `tuvx_tropo.json` | jO3_O1D, jO3_O, jNO2, jH2O2, jCH2O_a, jCH2O_b, jCH3OOH, jHNO3 | Tropospheric Ox-HOx-NOx-CO-CH4 chemistry for the global examples | No; published on the wiki |

The release also ships `tuvx_upper_atm.csv`, the default extension profile.

## TUV-x Update Interval

By default, chemistry calls TUV-x on every chemistry step. Photolysis rates
change on minute-to-hour time scales, while the dynamics `dt` may be a few
seconds, so for long integrations or small `dt` this is more often than
necessary. Set `config_tuvx_update_interval` (simulated seconds) in the
`&photolysis` namelist to update photolysis at a coarser cadence.

The first chemistry step always computes rates. After that, the photolysis
block runs only once at least the configured interval of simulated time has
accumulated since the last update. On the steps in between, the whole block
is skipped, for the fallback as well as for TUV-x: MICM keeps using the rate
parameters last set, and the `j_<rate>` fields keep their last values. The
default `0.0` updates every step.

With chemistry running every dynamics step, a 60 s interval at `dt = 3 s`
runs TUV-x once every 20 steps. The release examples use 600 s in the
supercell template's commented TUV-x block and 3600 s for the global
Chapman + NOx case.

## Column Extension Above MPAS Top

TUV-x can include a prescribed column above the MPAS model top so that UV
absorption by air and O3 above the domain is accounted for.
`config_tuvx_upper_column_mode` selects exactly one source:

| Mode | Upper column |
|------|--------------|
| `none` (default) | MPAS column only |
| `legacy_static` | One-dimensional profile from a CSV file, the same for every column |
| `spatial_climatology` | Per-cell monthly O3 from a NetCDF package on the run mesh |

`config_tuvx_top_extension` is a consistency flag: it must be `.true.` with
`legacy_static` or `spatial_climatology` and `.false.` with `none`. Each mode
accepts only its own input file (`config_tuvx_extension_file` or
`config_tuvx_prescribed_field_file`). Inconsistent combinations, or an
upper-column mode without `config_tuvx_config_file`, stop the run at
initialization. Neither extension mode changes prognostic `qO3`.

### Column stitching

With an extension, TUV-x is built on `nVertLevels + n_ext` grid sections (70
for the 60-level supercell with the default CSV). For each column:

- MPAS layers 1 to `nVertLevels` come from the host state as described above.
- Extension layers take midpoint values averaged from the extension edge
  values.
- Extension temperatures keep the profile's vertical gradient but are shifted
  by a constant so that the first extension midpoint equals the top MPAS
  midpoint temperature, which avoids a temperature step at the join.
- The edge at the join averages the top MPAS midpoint and the first extension
  midpoint, as for every other interior edge.
- Cloud optical depth is zero in the extension.
- Only the first `nVertLevels` rates are returned to MICM.

The first extension edge must coincide with the MPAS model top to within
0.5 m. Otherwise the photolysis update fails, and the log asks for the
upper-column input to be regenerated for the mesh.

### Static profile

```
&photolysis
    config_tuvx_top_extension = .true.
    config_tuvx_upper_column_mode = 'legacy_static'
    config_tuvx_extension_file = 'tuvx_upper_atm.csv'
/
```

The path is relative to the run directory. The file has a header line and one
row per layer edge, bottom-up:

```
z_km,T_K,n_air_molec_cm3,n_O3_molec_cm3
50.00,270.650,2.134997e+16,6.450000e+11
55.00,260.770,1.181062e+16,2.020000e+11
...
100.00,195.080,1.188474e+13,2.850000e+07
```

N data rows give N − 1 extension layers; at least two rows are required, and
heights must increase strictly. The default `micm_configs/tuvx_upper_atm.csv`
covers 50–100 km at 5 km spacing (10 layers), with temperature and air density
from the US Standard Atmosphere 1976 and O3 from the AFGL
mid-latitude-summer profile. It starts at the 50 km top of the idealized
supercell; `test_cases/chapman_nox_global` ships its own
`tuvx_upper_atm.csv`, which starts at 45 km. For another model top, supply a
file in the same format whose first row lies at that top.

### Spatial monthly O3 climatology

```
&photolysis
    config_tuvx_top_extension = .true.
    config_tuvx_upper_column_mode = 'spatial_climatology'
    config_tuvx_prescribed_field_file = 'o3_monthly_climatology.nc'
/
```

The file name above is an example; no package is distributed with
v2026.08.01. The package must:

- declare the schema `chempas-prescribed-field-package-v1`;
- contain the exact MPAS cell IDs and cell geometry (`indexToCellID`,
  `areaCell`, `latCell`, `lonCell`) of the run mesh;
- hold 12 monthly records with Gregorian climatology bounds;
- begin at the model top, with 11 layers above it.

The package supplies layer-mean O3 number density for each cell together with
the matching layer columns. Its reference atmosphere supplies the heights,
temperature, and air density of the upper layers, and O2 is derived from the
air density. Prognostic MPAS O3 is used at and below the model top, and
prescribed O3 only above it.

The run must use `config_calendar_type = 'gregorian'`. Each MPI task reads
only the cells it owns and caches the two monthly slabs that bracket the
current time. Values are interpolated linearly between month-midpoint anchors
computed from the actual Gregorian month lengths, with December wrapping to
January. Each monthly slab is checked when it is loaded: values must be finite
and non-negative, and density times layer thickness must reproduce the stored
layer column. Configuration or data errors are fatal; the spatial mode never
falls back to the CSV.

## Configuration

### Namelist options

All options below are in the `&photolysis` record. The mechanism itself is
selected with `config_micm_file` in `&chemistry`.

| Option | Default | Effect |
|--------|---------|--------|
| `config_tuvx_config_file` | `''` | TUV-x JSON configuration; a non-empty value enables TUV-x |
| `config_tuvx_upper_column_mode` | `'none'` | `none`, `legacy_static`, or `spatial_climatology` |
| `config_tuvx_top_extension` | `.false.` | Consistency flag; `.true.` with either extension mode |
| `config_tuvx_extension_file` | `''` | Extension CSV for `legacy_static` |
| `config_tuvx_prescribed_field_file` | `''` | NetCDF package for `spatial_climatology` |
| `config_tuvx_update_interval` | `0.0` | Simulated seconds between photolysis updates; `0.0` updates every chemistry step |
| `config_chemistry_use_grid_coords` | `.false.` | Per-cell solar geometry from `latCell` and `lonCell` |
| `config_chemistry_latitude` | `0.0` | Domain-wide latitude (degrees N) when grid coordinates are not used |
| `config_chemistry_longitude` | `0.0` | Domain-wide longitude (degrees E) when grid coordinates are not used |
| `config_j_no2_max` | `0.0` | Daytime maximum `jNO2` (s⁻¹) for the fallback; ignored when TUV-x is active |

### Run directory

In addition to the usual MPAS files, a run with TUV-x photolysis needs:

- the MICM mechanism named by `config_micm_file` and the matching TUV-x JSON
  file;
- the extension CSV or NetCDF package, if an upper-column mode is set;
- a `data` directory, or a link named `data`, holding the TUV-x data files.
  The shipped JSON files reference the wavelength grid, solar flux, cross
  sections, and quantum yields by relative paths under `data/` (for example
  `data/grids/wavelength/cam.csv`); these files come from `configs/tuvx/data`
  in the MUSICA source tree;
- the `j_<rate>` names in `stream_list.atmosphere.output`, if the rates
  should appear in history output.

TUV-x takes O3 at and below the model top from `qO3`, so the initial O3 field
sets the overhead ozone column. `scripts/init_lnox_o3.py` (uniform background
O3 for `lnox_o3.yaml`) and `scripts/init_chapman_nox.py` (altitude-dependent
O3, NO, and NO2 for the global Chapman + NOx case) ship in the release.

### Example: idealized supercell

The supercell template `test_cases/supercell/namelist.atmosphere` carries the
following block, together with `&lnox` settings, as a commented example:

```
&chemistry
    config_micm_file = 'lnox_o3.yaml'
/

&photolysis
    config_tuvx_config_file = 'tuvx_no2.json'
    config_tuvx_top_extension = .true.
    config_tuvx_upper_column_mode = 'legacy_static'
    config_tuvx_extension_file = 'tuvx_upper_atm.csv'
    config_tuvx_update_interval = 600.0
    config_j_no2_max = 0.01
    config_chemistry_latitude = 35.86
    config_chemistry_longitude = -97.93
/
```

The coordinates place the domain at Kingfisher, Oklahoma, and every column
shares that solar geometry. The template starts at `0000-01-01_00:00:00`,
after local sunset at these coordinates, so photolysis rates stay at zero
until sunrise; [Tutorial Chapter 2](../../tutorial/02-deep-convection.md)
sets an 18:00 UTC start in both namelists for daytime photolysis.
`config_j_no2_max` has no effect while TUV-x is active. The same template also carries an isotherm-gated lightning variant
and a commented Chapman block. The mechanism, TUV-x configuration, and
initialization script that the Chapman block names are not part of the
release. The released Chapman + NOx pair, `chapman_nox.yaml` with
`tuvx_chapman_nox.json`, includes the Chapman cycle.

### Example: global Chapman + NOx

`test_cases/chapman_nox_global/namelist.atmosphere` uses per-cell solar
geometry on the global mesh:

```
&chemistry
    config_micm_file = 'chapman_nox.yaml'
/

&photolysis
    config_tuvx_config_file = 'tuvx_chapman_nox.json'
    config_tuvx_top_extension = .true.
    config_tuvx_upper_column_mode = 'legacy_static'
    config_tuvx_extension_file = 'tuvx_upper_atm.csv'
    config_tuvx_update_interval = 3600.0
    config_chemistry_use_grid_coords = .true.
/
```

Its `stream_list.atmosphere.output` already lists `j_jNO2`, `j_jO2`,
`j_jO3_O`, and `j_jO3_O1D`.

## Current Limitations

- **No cloud shadows.** Each column is an independent one-dimensional TUV-x
  calculation. A cloud attenuates photolysis only in its own column; at a
  slant solar angle it has no effect on the neighboring columns the direct
  beam passes through, so clouds cast no shadows to the side.
- **Liquid clouds only.** Cloud optical depth uses `qc` and `qr`; ice, snow,
  and graupel are not included. Effective radii are fixed, the optical depth
  does not vary with wavelength, and the single-scattering albedo and
  asymmetry factor are constants.
- **No aerosols.** Aerosol extinction is not included.
- **Fixed Earth–Sun distance.** TUV-x is run with an Earth–Sun distance of
  1 AU throughout the year.
- **Surface albedo from the configuration.** Surface albedo is set in the
  TUV-x JSON (0.10 in the shipped files) and does not come from MPAS surface
  fields.
- **One wavelength grid.** The cloud radiator is sized for the 102-section CAM
  wavelength grid (`data/grids/wavelength/cam.csv`), which every shipped TUV-x
  configuration uses. TUV-x configurations must use the same grid.
- **Single-rate fallback.** The `cos(SZA)` fallback supplies only `jNO2`.
- **Cost.** TUV-x runs for every sunlit column at each update, clear or
  cloudy. `config_tuvx_update_interval` is the control for its cost.
- **Spatial climatology structure.** The package format is fixed at 12
  months and 11 layers above the model top, runs must use the Gregorian
  calendar, and no package ships with v2026.08.01.

## See Also

- [Chapter 8: Chemistry Coupling](../../users-guide/08-chemistry-coupling.md)
  — the chemistry step sequence and photolysis internals
- [Appendix B: Model Namelist Options](../../users-guide/0B-model-namelist.md)
  — section B.14 lists every `&chemistry`, `&photolysis`, and `&lnox` option
- [LNOx integration](LNOX_INTEGRATION.md) — the lightning-NO source used with
  `lnox_o3.yaml`
- [MUSICA/MICM integration](../musica/MUSICA_INTEGRATION.md)
- [Chemistry Test Cases](https://github.com/NCAR/CheMPAS-A/wiki/Chemistry-Test-Cases)
  in the CheMPAS-A wiki
- [CheMPAS-A v2026.08.01](https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01)
