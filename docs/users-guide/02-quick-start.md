# Chapter 2: CheMPAS-A Quick Start Guide

This chapter gives the shortest public path from the tagged MVP source to a
chemistry-enabled run. The model implementation is in the CheMPAS-A source
repository; the public wiki carries the declarative example inputs and their
data contracts.

## Obtain the MVP Source and Examples

Clone the immutable MVP release candidate and the companion wiki:

```bash
git clone --branch v2026.08.01-rc2 --depth 1 \
  https://github.com/NCAR/CheMPAS-A.git
git clone https://github.com/NCAR/CheMPAS-A.wiki.git
```

The wiki's [Examples](https://github.com/NCAR/CheMPAS-A/wiki/Examples) page
maps each supported example to its namelist, streams, mechanism, photolysis,
and emissions files. Large meshes, meteorological inputs, inventories, and
prepared model states remain outside Git; their providers, selections, and
checksums are recorded in
[Data and Provenance](https://github.com/NCAR/CheMPAS-A/wiki/Data-and-Provenance).

## Build Process

CheMPAS-A uses the normal MPAS dependencies: compatible C and Fortran
compilers, MPI, NetCDF-C, NetCDF-Fortran, PnetCDF, and PIO. Chemistry builds
also require the pinned MUSICA-Fortran package with MICM, TUV-x, and MIEM.
[Chapter 3](03-building.md) gives complete Ubuntu, macOS LLVM, and Derecho
dependency and compiler recipes; the public wiki's
[Building](https://github.com/NCAR/CheMPAS-A/wiki/Building) page is the concise
MVP recipe.

After exporting the installation prefixes, build the initialization core and
then the chemistry-enabled atmosphere core from clean boundaries:

```bash
export NETCDF=/path/to/netcdf
export NETCDFF=/path/to/netcdf-fortran
export PNETCDF=/path/to/pnetcdf
export PIO=/path/to/pio
export MUSICA_PREFIX=/path/to/musica-install
export PKG_CONFIG_PATH="${MUSICA_PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"

cd CheMPAS-A

make clean CORE=init_atmosphere
make -j8 gfortran CORE=init_atmosphere OPENMP=false \
  PIO="$PIO" NETCDF="$NETCDF" NETCDFF="$NETCDFF" PNETCDF="$PNETCDF" \
  PRECISION=double

make clean CORE=atmosphere
make -j8 gfortran CORE=atmosphere OPENMP=false \
  PIO="$PIO" NETCDF="$NETCDF" NETCDFF="$NETCDFF" PNETCDF="$PNETCDF" \
  PRECISION=double MUSICA=true
```

A successful build produces `init_atmosphere_model`, `build_tables`, and
`atmosphere_model`. The command above is the qualified Ubuntu path. On macOS,
use the `llvm` target with the flang-built dependency stack; on Derecho, use
the `cray` target with the Cray programming environment. Both procedures,
including construction and verification of the pinned MUSICA package, are in
[Chapter 3](03-building.md#35-documented-build-environments).

## Stage a First Chemistry Run

Start with the wiki's
[Idealized Test Cases](https://github.com/NCAR/CheMPAS-A/wiki/Idealized-Test-Cases)
or [Chemistry Test Cases](https://github.com/NCAR/CheMPAS-A/wiki/Chemistry-Test-Cases).
Each page identifies the official MPAS archive to download and the matching
files under `CheMPAS-A.wiki/examples/`.

A run directory normally contains:

```text
atmosphere_model
LANDUSE.TBL
namelist.atmosphere
streams.atmosphere
stream_list.atmosphere.output
<initial-condition>.nc
<graph>.part.8
<MICM mechanism>.yaml
<TUV-x configuration>.json       # when photolysis is enabled
data/                            # pinned TUV-x data
<MIEM configuration>.yaml        # when emissions are enabled
<inventory>.nc                   # when emissions are enabled
```

Use the supplied eight-rank partition and launch from the staged directory:

```bash
mpiexec -n 8 ./atmosphere_model
```

Check `log.atmosphere.0000.out` for the source revision, enabled chemistry
components, runtime-injected fields, mesh validation, and normal completion.
Chemistry currently requires exactly one local MPAS block on each MPI task.

## Chemistry State and Output Units

CheMPAS-A transports and restarts `q<species>` as dry-air mass mixing ratio.
A history stream may additionally request output-only volume-mixing-ratio
diagnostics:

```fortran
&chemistry
    config_micm_file = 'mechanism.yaml'
    config_chem_tracer_output_unit = 'ppbv'
    config_chem_tracer_output_overrides = 'O3=ppbv,NO=ppbv,NO2=ppbv'
/
```

The companion fields are named `vmr_<species>`. They do not replace the
authoritative transported state. See [Runtime Chemistry Tracers](07-runtime-tracers.md)
and [Chemistry Coupling](08-chemistry-coupling.md) for the state and unit
contracts.

## Reproduce the Global MVP

The public
[Global Chemistry and Emissions](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions)
guide reconstructs the 24-hour x1.40962 demonstration with three descriptive
scenarios:

- No Surface Emissions
- Anthropogenic Emissions
- Anthropogenic + Fire Emissions

All three use identical meteorology, chemistry, photolysis, and initial state;
only the declared surface sources differ. The guide links the exact namelists,
streams, reduced mechanism, TUV-x configuration, MIEM configurations, and data
manifest. The corresponding qualification evidence is retained in the
[MVP record](../chempas/mvp/MVP_PRE_RELEASE.md).

The demonstration validates coupled process integration and source
bookkeeping. It is not a production air-quality forecast or a chemically
spun-up global-composition product.
