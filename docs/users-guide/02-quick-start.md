# Chapter 2: CheMPAS-A Quick Start Guide

This chapter gives the shortest public path from the tagged MVP source to a
chemistry-enabled run. The model implementation is in the CheMPAS-A source
repository; the public wiki carries the declarative example inputs and their
data contracts.

For the three bounded demonstrations, [Running the Examples with
Docker](../tutorial/docker.md) gives the image build and launch commands.
The native workflow below supports the full
[public example collection](../tutorial/running-examples.md).

## Obtain the MVP Source and Examples

Clone the MVP release and the companion wiki:

```bash
git clone --branch v2026.08.01 --depth 1 \
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
[Building](https://github.com/NCAR/CheMPAS-A/wiki/Building) page carries the
same recipes.

First select a platform recipe in Chapter 3. On Derecho, the
[shared installation](03-building.md#391-option-a-use-the-shared-pio-and-musica-installation)
sets the compiler modules and library prefixes in one step:

```bash
source /glade/work/fillmore/chempas-a/ncarenv-25.10-gcc/env.sh
```

For a private installation, export its prefixes and the platform's Make
target. For example, Ubuntu uses the following settings; retain the settings
from Chapter 3 when building on macOS or Derecho:

```bash
export NETCDF=/path/to/netcdf
export NETCDFF=/path/to/netcdf-fortran
export PNETCDF=/path/to/pnetcdf
export PIO=/path/to/pio
export MUSICA_PREFIX=/path/to/musica-install
export CHEMPAS_MAKE_TARGET=gfortran
```

Verify the pinned MUSICA metadata as described in
[Section 3.6](03-building.md#36-build-the-pinned-musica-dependency), including
both possible installation directories:

```bash
export PKG_CONFIG_PATH="${MUSICA_PREFIX}/lib64/pkgconfig:${MUSICA_PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
```

Build the initialization core and then the chemistry-enabled atmosphere core
from clean boundaries:

```bash
cd CheMPAS-A

make clean CORE=init_atmosphere
make -j8 "$CHEMPAS_MAKE_TARGET" CORE=init_atmosphere OPENMP=false \
  PIO="$PIO" NETCDF="$NETCDF" NETCDFF="$NETCDFF" PNETCDF="$PNETCDF" \
  PRECISION=double

make clean CORE=atmosphere
make -j8 "$CHEMPAS_MAKE_TARGET" CORE=atmosphere OPENMP=false \
  PIO="$PIO" NETCDF="$NETCDF" NETCDFF="$NETCDFF" PNETCDF="$PNETCDF" \
  PRECISION=double MUSICA=true
```

A successful build produces `init_atmosphere_model`, `build_tables`, and
`atmosphere_model`. Ubuntu and Derecho use `gfortran`; Derecho requires
GCC 14.3.0 with Cray MPICH and the NCAR MPI wrappers. On macOS, use `llvm`
with the flang-built dependency stack. The platform procedures, including
construction and verification of the pinned MUSICA package, are in
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
<graph>.part.<MPI-ranks>
<MICM mechanism>.yaml
<TUV-x configuration>.json       # when photolysis is enabled
data/                            # pinned TUV-x data
<MIEM configuration>.yaml        # when emissions are enabled
<inventory>.nc                   # when emissions are enabled
```

Copy or link `LANDUSE.TBL` from
`CheMPAS-A/src/core_atmosphere/physics/physics_wrf/files/`. When TUV-x is
enabled, link the pinned MUSICA `configs/tuvx/data` directory as `data`.
The shared Derecho installation provides the same data at
`$MUSICA_PREFIX/share/tuvx/data`.

Use the rank count matching the partition and the namelist's decomposition
prefix. For the eight-rank x1.40962 example, launch from the staged directory:

```bash
mpiexec -n 8 ./atmosphere_model
```

Check `log.atmosphere.0000.out` for the source revision, enabled chemistry
components, runtime-injected fields, mesh validation, and normal completion.
Chemistry currently requires exactly one local MPAS block on each MPI task.
Leave the supplied examples on automatic block decomposition. The
[manual example workflow](../tutorial/running-examples.md) covers
initialization, clocks, and case-specific staging.

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
only the declared surface sources differ. All three also run with
`config_physics_suite = 'none'`, so there is no boundary-layer mixing,
convection, or cloud, and TUV-x runs clear-sky. The guide links the exact
namelists, streams, reduced mechanism, TUV-x configuration, MIEM
configurations, and data manifest.

The demonstration validates coupled process integration and source
bookkeeping. It is not a production air-quality forecast or a chemically
spun-up global-composition product.
