# Chapter 3: Building CheMPAS-A

## 3.1 Prerequisites

To build CheMPAS-A, compatible C and Fortran compilers are required; the
chemistry-enabled build also requires a compatible C++ compiler for the
MUSICA/MICM/MIEM dependency closure. Additionally, the MPAS software relies on
the PIO parallel I/O library to read and write model fields, and the PIO
library requires the standard netCDF library as well as the parallel-netCDF
library from Argonne National Laboratory. All libraries must be compiled with
the compiler/ABI combination used to build CheMPAS-A. Section 3.2 summarizes
the basic procedure of installing the required I/O libraries.

In order for the MPAS makefiles to find the PIO, parallel-netCDF, and netCDF
include files and libraries, the environment variables `PIO`, `PNETCDF`, and
`NETCDF` should be set to their root installation directories. Set `NETCDFF`
as well when NetCDF-Fortran has a different prefix; otherwise it defaults to
`NETCDF` in the documented commands.

An MPI installation such as MPICH or OpenMPI is also required, and there is no option to build a serial version of the MPAS executables. MPAS-Atmosphere v5.0 introduces the capability to use hybrid parallelism using MPI and OpenMP; however, the use of OpenMP *should be considered experimental* and generally does not offer any performance advantage. The primary reason for releasing a shared-memory capability is to make this code available to collaborators for future development.

## 3.2 Compiling I/O Libraries

> **IMPORTANT NOTE:** *The instructions provided in this section for installing libraries have been successfully used by MPAS developers, but due to differences in library versions, compilers, and system configurations, it is recommended that users consult documentation provided by individual library vendors should problems arise during installation. The MPAS developers cannot assume responsibility for third-party libraries.*

The verified CheMPAS-A 26.08 GNU/Linux environment uses netCDF-C 4.10.1,
netCDF-Fortran 4.6.3, PnetCDF 1.14.1, and PIO 2.6.9. Other compatible versions
may work, but the repository preflight and a clean link test are authoritative
for a particular toolchain. NetCDF and PnetCDF must be installed before PIO.

### 3.2.1 NetCDF

NetCDF releases may be downloaded from the current
[Unidata distribution site](https://downloads.unidata.ucar.edu/netcdf/). The
Unidata documentation provides detailed instructions for building the netCDF C
and Fortran libraries; both interfaces are needed by PIO. If netCDF-4 support
is desired, zlib and HDF5 must be installed first. *Before proceeding to
compile PIO the `NETCDF` environment variable should be set to the netCDF root
installation directory.*

### 3.2.2 Parallel-NetCDF

Parallel-NetCDF releases may be downloaded from the current
[PnetCDF download page](https://parallel-netcdf.github.io/wiki/Download.html).
*Before proceeding to compile PIO the `PNETCDF` environment variable should be
set to the parallel-NetCDF root installation directory.*

### 3.2.3 PIO

The reference build uses PIO 2.6.9. The current CheMPAS-A `Makefile` detects
the available PIO API during its link test and defines the appropriate compile
flag automatically; the legacy `USE_PIO2=true` option is deprecated and
ignored.

PIO 1.x remains a legacy compatibility path. The historically supported 1.x
releases may be obtained from:
- <https://github.com/NCAR/ParallelIO/releases/tag/pio1_7_1>
- <https://github.com/NCAR/ParallelIO/releases/tag/pio1_9_23>

The PIO 2.x library versions support integrated performance timing with the GPTL library; however, the MPAS infrastructure does not currently provide calls to initialize this library when it is used in PIO 2.x. Therefore, it is recommended to add `-DPIO_ENABLE_TIMING=OFF` when running the cmake command to build PIO 2.x versions.

After PIO is built and installed the `PIO` environment variable should be set to the directory where PIO was installed. Recent versions of PIO support the specification of an installation prefix, while some older versions do not, in which case the `PIO` environment variable should be set to the directory where PIO was compiled.

## 3.3 Compiling MPAS

> **IMPORTANT NOTE:** *Before compiling MPAS, the `NETCDF`, `PNETCDF`, and
> `PIO` environment variables must be set to the library installation
> directories described above. Set `NETCDFF` too when NetCDF-Fortran uses a
> different prefix.*

The supported chemistry-enabled path uses the top-level `Makefile`. (The
repository also retains a CMake path for non-chemistry work; it does not compile
the CheMPAS chemistry sources.) The Makefile contains each supported compiler
configuration as a separate target, selected on the command line, e.g.,

```
make gfortran
```

to build the code using the GNU Fortran and C compilers. Representative current
targets are listed below. The top-level `Makefile` is the complete authority
and also retains platform-specific and deprecated targets; the current
reference builds are `gfortran` and `llvm`.

| Target | Fortran compiler | C compiler | MPI wrappers |
|--------|-----------------|------------|--------------|
| `xlf` | xlf90 | xlc | mpxlf90 / mpcc |
| `gnu`, `gfortran` | gfortran | gcc | mpif90 / mpicc |
| `llvm` | flang | clang | mpifort / mpicc |
| `nvhpc` | nvfortran | nvc | mpifort / mpicc |
| `pgi` | pgf90 | pgcc | mpif90 / mpicc |
| `ifort` | ifort | icc | mpif90 / mpicc |
| `intel` | ifx | icx | mpifort / mpicc |
| `ftn`, `cray` | Cray wrapper | Cray wrapper | ftn / cc |

The MPAS framework supports multiple *cores* -- currently a shallow water model, an ocean model, a land-ice model, a non-hydrostatic atmosphere model, and a non-hydrostatic atmosphere initialization core -- so the build process must be told which core to build. This is done by either setting the environment variable `CORE` to the name of the model core to build, or by specifying the core to be built explicitly on the command-line when running make. For the atmosphere core, for example, one may run either:

```
setenv CORE atmosphere
make gfortran
```

or:

```
make gfortran CORE=atmosphere
```

If the `CORE` environment variable is set and a core is specified on the command-line, the command-line value takes precedence; if no core is specified, either on the command line or via the `CORE` environment variable, the build process will stop with an error message stating such. Assuming compilation is successful, the model executable, named `${CORE}_model` (e.g., `atmosphere_model`), should be created in the top-level MPAS directory.

In order to get a list of available cores, one can simply run the top-level `Makefile` without setting the `CORE` environment variable or passing the core via the command-line:

```
> make
( make error )
make[1]: Entering directory '/scratch/MPAS-Release'

Usage: make target CORE=[core] [options]

Example targets:
    ifort
    gfortran
    xlf
    pgi

Available Cores:
    atmosphere
    init_atmosphere
    landice
    ocean
    seaice
    sw
    test

Available Options:
    DEBUG=true       - builds debug version. Default is optimized version.
    USE_PAPI=true    - builds version using PAPI for timers. Default is off.
    TAU=true         - builds version using TAU hooks for profiling. Default is off.
    AUTOCLEAN=true   - forces a clean of infrastructure prior to build new core.
    GEN_F90=true     - Generates intermediate .f90 files through CPP, and builds with them.
    TIMER_LIB=opt    - Selects the timer library interface to be used for profiling the model.
                       TIMER_LIB=native - Uses native built-in timers in MPAS
                       TIMER_LIB=gptl   - Uses gptl for the timer interface
                       TIMER_LIB=tau    - Uses TAU for the timer interface
    OPENMP=true      - builds and links with OpenMP flags. Default is to not use OpenMP.
    OPENACC=true     - builds and links with OpenACC flags when supported by the target.
    PRECISION=double - builds with default double-precision real kind. Default is single-precision.
    SHAREDLIB=true   - generates position-independent code suitable for a shared library.

************ ERROR ************
No CORE specified. Quitting.
************ ERROR ************
```

## 3.4 Selecting Model Precision

Beginning with version 2.0, MPAS-Atmosphere can be compiled and run in single precision, offering faster model execution and smaller input and output files. In CheMPAS-A, single precision is the default when `PRECISION` is omitted; specifying `PRECISION=single` is accepted but unnecessary. To compile a double-precision executable, add `PRECISION=double` to the build command, e.g.,

```
make gfortran CORE=atmosphere PRECISION=double
```

Regardless of which precision the CheMPAS-A `init_atmosphere` and `atmosphere` cores were compiled with, either single- or double-precision input files may be used. In general, the MPAS infrastructure should correctly detect the precision of input files, but one may also explicitly specify the precision of files in an input stream by adding the `precision` attribute to the stream definition as described in [Section 5.2](05-configuring-io.md#52-optional-stream-attributes).

## 3.5 Validated MVP Platform

The public MVP validates the GNU/Linux path with GCC/gfortran. The top-level
Makefile retains other compiler targets, including `llvm`, but macOS validation
is deferred and is not part of the release-candidate support claim.

Set the dependency prefixes in the shell that invokes `make`:

```bash
export NETCDF=/path/to/netcdf
export NETCDFF=/path/to/netcdf-fortran
export PNETCDF=/path/to/pnetcdf
export PIO=/path/to/pio
```

`NETCDFF` may equal `NETCDF` when the C and Fortran libraries share one
prefix. The validated Ubuntu build used GNU Fortran 15.2.0, Open MPI 5.0.10,
NetCDF-C 4.10.1, NetCDF-Fortran 4.6.3, PnetCDF 1.14.1, and PIO 2.6.9.
Other compatible versions may work.

The public wiki's
[Building](https://github.com/NCAR/CheMPAS-A/wiki/Building) page gives the
concise, release-specific dependency and build recipe.

## 3.6 Building with Chemistry (MUSICA) Support

Runtime species discovery, MUSICA/MICM coupling, MIEM offline emissions, and
TUV-x photolysis require MUSICA-Fortran 0.16.5 at source revision
`1403e3d22717bc87f3bf9d0aa591caf039c92bbc`, built with MIEM and TUV-x enabled.
The CheMPAS-A Makefile verifies the MUSICA version, MUSICA revision, MIEM
revision, and enabled-feature metadata while parsing the build.

Put the pinned package first in `PKG_CONFIG_PATH`:

```bash
export MUSICA_PREFIX=/path/to/musica-install
export PKG_CONFIG_PATH="${MUSICA_PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"

pkg-config --modversion musica-fortran
pkg-config --variable=source_revision musica-fortran
pkg-config --variable=miem_revision musica-fortran
pkg-config --variable=miem_enabled musica-fortran
pkg-config --variable=tuvx_enabled musica-fortran
```

Build the initialization core first. Then clean the shared framework before
building the chemistry-enabled atmosphere core:

```bash
make clean CORE=init_atmosphere
make -j8 gfortran CORE=init_atmosphere OPENMP=false \
  PIO="$PIO" NETCDF="$NETCDF" NETCDFF="$NETCDFF" PNETCDF="$PNETCDF" \
  PRECISION=double

make clean CORE=atmosphere
make -j8 gfortran CORE=atmosphere OPENMP=false \
  PIO="$PIO" NETCDF="$NETCDF" NETCDFF="$NETCDFF" PNETCDF="$PNETCDF" \
  PRECISION=double MUSICA=true
```

Without `MUSICA=true`, the chemistry hooks compile out and the chemistry
namelist records are ignored at runtime. MUSICA-Fortran and CheMPAS-A must use
the same Fortran compiler family and compatible NetCDF libraries; compiler
module files are not portable across toolchains.

For the runtime features enabled by this build, see
[Chapter 7](07-runtime-tracers.md) and
[Chapter 8](08-chemistry-coupling.md).

## 3.7 Cleaning

To remove all files that were created when the model was built, including the model executable itself, make may be run for the `clean` target:

```
make clean
```

As with compiling, the core to be cleaned is specified by the `CORE` environment variable, or by specifying a core explicitly on the command-line with `CORE=`.
