# Running the Public Examples

This workflow follows the wiki's [Getting Started](https://github.com/NCAR/CheMPAS-A/wiki/Getting-Started)
and [Examples](https://github.com/NCAR/CheMPAS-A/wiki/Examples) guides. Build
`init_atmosphere_model`, `build_tables`, and a MUSICA-enabled
`atmosphere_model` using [Building CheMPAS-A](../users-guide/03-building.md).
For the three bounded container demonstrations, use the separate
[Docker workflow](docker.md).

## Obtain the example inputs

Clone the wiki alongside the
[`v2026.08.01` model source](https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01):

```bash
git clone https://github.com/NCAR/CheMPAS-A.wiki.git
```

The wiki clone contains documentation and declarative inputs under
`examples/`. Executables, initializer scripts, and Docker assets come from
the model source repository. Large meshes, initial states, and emissions
inventories are obtained separately. Follow
[Data and Provenance](https://github.com/NCAR/CheMPAS-A/wiki/Data-and-Provenance)
for the provider URLs, preparation contracts, and checksums.

| Case | Wiki input directory | What it exercises | Nominal run |
|---|---|---|---|
| [Mountain-wave ABBA](https://github.com/NCAR/CheMPAS-A/wiki/Idealized-Test-Cases#user-content-mountain-wave-and-jw-abba) | `examples/idealized/mountain-wave/` | Runtime tracers, transport, reversible toy chemistry | 5 hours |
| [JW baroclinic-wave ABBA](https://github.com/NCAR/CheMPAS-A/wiki/Idealized-Test-Cases#user-content-mountain-wave-and-jw-abba) | `examples/idealized/jw-baroclinic-wave/` | Global transport, runtime tracers, restart streams | 16 days |
| [Supercell lightning NOx](https://github.com/NCAR/CheMPAS-A/wiki/Idealized-Test-Cases#user-content-supercell-lightning-nox) | `examples/idealized/supercell-lnox/` | Lightning source, fixed solar coordinates, TUV-x `jNO2` | 60 seconds |
| [Global Chapman + NOx](https://github.com/NCAR/CheMPAS-A/wiki/Chemistry-Test-Cases) | `examples/chemistry/chapman-nox-global/` | Spatial solar geometry, six chemistry species, TUV-x upper extension | 24 hours |
| [Global emissions scenarios](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions) | `examples/global-emissions/` | Prescribed upper O3, CAMS/FINN sources, scenario differences | 24 hours each |

Supercell ABBA uses the release's `test_cases/supercell/` configuration with
`micm_configs/abba.yaml`; see [the supercell tutorial](02-deep-convection.md#25-run-with-the-abba-mechanism).
It is also one of the three Docker cases. Docker packages bounded variants
of Supercell ABBA, Supercell LNOx, and Global Chapman + NOx, with minimal
output lists. The full wiki collection includes additional cases and fuller
output lists.

## Create a run directory

An atmosphere run directory normally contains:

```text
atmosphere_model
LANDUSE.TBL
namelist.atmosphere
streams.atmosphere
stream_list.atmosphere.output
<initial-condition>.nc
<graph>.part.<MPI-ranks>
<MICM mechanism>.yaml
<TUV-x configuration>.json     # when photolysis is enabled
data/                         # pinned MUSICA TUV-x data, when enabled
<MIEM configuration>.yaml      # when emissions are enabled
<inventory>.nc                # when emissions are enabled
```

Copy or link `LANDUSE.TBL` from
`CheMPAS-A/src/core_atmosphere/physics/physics_wrf/files/LANDUSE.TBL`.
Keep the case's namelist, streams, output list, and chemistry files together;
every filename must match the corresponding configuration entry exactly.

The example TUV-x JSON paths are relative to `data/`. Link the data from
the [pinned MUSICA source](../users-guide/03-building.md#36-build-the-pinned-musica-dependency):

```bash
ln -s /path/to/MUSICA-CheMPAS-A/configs/tuvx/data data
```

For the shared Derecho installation, source its `env.sh` and use its
installed TUV-x data instead:

```bash
source /glade/work/fillmore/chempas-a/ncarenv-25.10-gcc/env.sh
ln -s "$MUSICA_PREFIX/share/tuvx/data" data
```

Use the same compiler, MPI, and I/O modules in every PBS run script as were
used for the executable and its libraries.

## Prepare the initial state

### Mountain-wave and JW ABBA

Download the matching official NCAR archive:

- [Mountain wave](https://www2.mmm.ucar.edu/projects/mpas/test_cases/v7.0/mountain_wave.tar.gz)
- [JW baroclinic wave](https://www2.mmm.ucar.edu/projects/mpas/test_cases/v7.0/jw_baroclinic_wave.tar.gz)

Extract it into an empty working directory, then copy the matching wiki
example directory's files over the archive's configurations. Stage
`init_atmosphere_model`, `atmosphere_model`, `build_tables`, and the required
physics tables. Run `init_atmosphere_model` with the rank count matching the
selected partition. Confirm that its output filename matches the atmosphere
input stream before launching the atmosphere core.

The mountain-wave example uses `mtn_wave_grid.nc`, `mtn_wave_init.nc`, and
`mtn_wave.graph.info.part.N`. The JW example uses `x1.40962.grid.nc`,
`x1.40962.init.nc`, and `x1.40962.graph.info.part.N`. Expect runtime
registration of A, B, and AB and their dry-air mass mixing ratios in the
history `scalars` array.

### Supercell lightning NOx

Extract the [supercell archive](https://www2.mmm.ucar.edu/projects/mpas/test_cases/v7.0/supercell.tar.gz)
and stage the complete `examples/idealized/supercell-lnox/` inputs. These
include the initialization files, 60-level vertical grid, mechanism,
photolysis JSON, upper-atmosphere CSV, and output list. Link `data/` as
described above and run `init_atmosphere_model` with a matching partition.

Initialize NO and NO2 to zero and O3 to 50 ppbv using the release script
from the run directory; replace `/path/to/CheMPAS-A` with the source checkout:

```bash
python /path/to/CheMPAS-A/scripts/init_lnox_o3.py -i supercell_init.nc
```

Without that step all three tracers start at zero. The wiki namelists start
at `0000-01-01_18:00:00`, in daylight at the fixed solar coordinates
35.86 degrees N, 97.93 degrees W. Their one-minute duration and 30 s output
interval provide a short coupling check. The release template used by Docker
starts at 00:00 UTC, after local sunset there, and defaults to two hours.
The [longer supercell tutorial](02-deep-convection.md#26-deep-convection-the-lightning-nox--o₃-mechanism)
sets a daytime start and explores lightning production over a developed storm.

### Global Chapman + NOx

The JW archive supplies the grid and eight-rank partition but no initial
state. Generate `x1.40962.init.nc` using the wiki's
`examples/idealized/jw-baroclinic-wave/namelist.init_atmosphere` and
`streams.init_atmosphere`, running `init_atmosphere_model` on eight ranks.
Then create a separate chemistry initial state:

```bash
python /path/to/CheMPAS-A/scripts/init_chapman_nox.py \
  -i x1.40962.init.nc -o x1.40962.chapman_nox_init.nc
```

Stage all files from `examples/chemistry/chapman-nox-global/`, the chemistry
initial state, `x1.40962.graph.info.part.8`, `LANDUSE.TBL`, and the executable.
Link `data/` from pinned MUSICA. Use this case's upper-atmosphere CSV, which
begins at the 45 km JW lid; the supercell CSV begins at 50 km.

The initializer writes five tracers; the sixth, `qO1D`, is created at zero
by the model. The run uses a 450 s dynamics step, 3600 s TUV-x updates,
cell-local solar coordinates, and hourly output. Check all six species and
four photolysis diagnostics. [Chapter 4](04-stratosphere.md) describes the
profiles and output analysis.

### Global emissions scenarios

Use the wiki's [Global Chemistry and Emissions](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions)
guide and [data manifest](https://raw.githubusercontent.com/wiki/NCAR/CheMPAS-A/examples/global-emissions/data-manifest.json)
to prepare the meteorology, expanded chemistry initial state, exact-grid
inventories, and prescribed upper-O3 package. Create a separate run directory
for each scenario:

- **No Surface Emissions:** `no-surface-emissions/namelist.atmosphere` and
  its output list; `config_miem_file` is empty.
- **Anthropogenic Emissions:** `anthropogenic/namelist.atmosphere` and its
  output list, `global_mvp_cams.yaml`, and `miem_inventory.cams.nc`.
- **Anthropogenic + Fire Emissions:** `anthropogenic-fire/namelist.atmosphere`
  and its output list, `global_mvp_cams_finn.yaml`, and both
  `miem_inventory.cams.nc` and `miem_inventory.finn.nc`.

All three stage the common `streams.atmosphere`,
`global_cams_tropo_ch4nox.yaml`, `tuvx_tropo.json`, pinned TUV-x `data/`,
`prescribed-o3.nc`, `x1.40962.global-miem.init.nc`,
`x1.40962.graph.info.part.8`, `LANDUSE.TBL`, and `atmosphere_model`.
They run on eight ranks from `2024-07-01_00:00:00` to
`2024-07-02_00:00:00`, with identical meteorology and initial chemistry.
All use `config_physics_suite = 'none'` and clear-sky TUV-x.

## Match the decomposition and clock

For `N` MPI ranks, the namelist's decomposition prefix must resolve to a
file ending in `.part.N`. For example:

```text
config_block_decomp_file_prefix = 'x1.40962.graph.info.part.'
x1.40962.graph.info.part.8
```

Chemistry requires exactly one local MPAS block per MPI task. Leave the
examples on automatic block decomposition and do not request multiple local
blocks.

MIEM requires a Gregorian calendar and inventory timestamps covering the
entire run without extrapolation. Idealized non-emissions cases may use the
conventional MPAS year-zero clock. The initialization `xtime`, atmosphere
start time, streams, and inventory timestamps must agree. If changing the
start time, regenerate or prepare the initial state for that time as well.

## Launch and check the output

Run from the staged directory, using the rank count for its partition. For
an eight-rank example:

```bash
mpiexec -n 8 ./atmosphere_model
```

Check `log.atmosphere.0000.out` for the source revision, enabled components,
runtime species and diagnostics, mesh validation, normal completion, and
`Critical error messages = 0`. Confirm that requested chemistry and
photolysis fields are present and finite. Before a rerun, archive the existing
output and logs; the native examples do not provide Docker's automatic
output archiving.

Record input hashes, compiler and dependency versions, the executable hash,
decomposition, clock, and output units using the wiki's
[Reproducibility Checklist](https://github.com/NCAR/CheMPAS-A/wiki/Reproducibility-Checklist).
ABBA tests coupling and transport, Chapman + NOx tests reduced
photochemistry, and the global emissions scenarios test process integration
and source attribution. Their idealized initial chemistry and reduced
mechanisms do not establish production air-quality performance.
