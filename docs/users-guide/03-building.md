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

## 3.5 Documented Build Environments

The build is organized around three environments. The Ubuntu toolchain is the
MVP release-qualification environment. The macOS and Derecho recipes preserve
the same dependency pins and Makefile contract while selecting their native
compiler stacks.

| Environment | Make target | Compiler family | Dependency source |
|---|---|---|---|
| Ubuntu 24.04 | `gfortran` | GCC/gfortran with Open MPI | conda-forge plus PIO from source |
| macOS | `llvm` | Apple clang/clang++ and Homebrew LLVM flang | Homebrew plus flang-built Fortran libraries |
| Derecho CPU | `cray` | Cray `cc`, `CC`, and `ftn` wrappers | `ncarenv` I/O modules plus private PIO and MUSICA installs |

Never reuse `.mod` or object files between these environments. In particular,
gfortran, flang, and Cray Fortran module files are mutually incompatible. Use a
different install and build directory for each compiler family, and run
`make clean CORE=<core>` before changing target or build options.

## 3.6 Build the Pinned MUSICA Dependency

Runtime species discovery, MUSICA/MICM coupling, MIEM offline emissions, and
TUV-x photolysis require the exact source closure below. A matching version
number alone is not sufficient.

| Component | Required revision |
|---|---|
| MUSICA-Fortran | `1403e3d22717bc87f3bf9d0aa591caf039c92bbc` (`0.16.5`) |
| MICM | `bb57684a2047f0e58f30b199366294af879e8597` |
| MIEM | `9fdf14a189262eecb677862d877ab72b06c95e21` |
| MechanismConfiguration | `82c159ae6d74934318ffd6c405a45c2159065b12` |
| TUV-x | `bbf7dd9a144fa0f0294b3779f3f993818638e20c` |

Obtain the MUSICA source once per platform:

```bash
export MUSICA_REV=1403e3d22717bc87f3bf9d0aa591caf039c92bbc

git clone --branch feature/miem-scalability-fortran --single-branch \
  https://github.com/NCAR/MUSICA.git MUSICA-CheMPAS-A
git -C MUSICA-CheMPAS-A checkout --detach "$MUSICA_REV"
test "$(git -C MUSICA-CheMPAS-A rev-parse HEAD)" = "$MUSICA_REV"
```

Each platform section below defines `MUSICA_PREFIX` and configures this source
with the appropriate compilers. All three builds use static libraries, enable
the Fortran interface, MICM, MIEM, and TUV-x, and disable CARMA, MIAM, and
`fmt`. `FETCHCONTENT_TRY_FIND_PACKAGE_MODE=NEVER` ensures the declared
component revisions are fetched instead of silently reusing same-named system
packages.

After installation, put the pinned package first and verify the metadata before
building CheMPAS-A:

```bash
export PKG_CONFIG_PATH="${MUSICA_PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"

test "$(pkg-config --modversion musica-fortran)" = 0.16.5
test "$(pkg-config --variable=source_revision musica-fortran)" = "$MUSICA_REV"
test "$(pkg-config --variable=micm_revision musica-fortran)" = \
  bb57684a2047f0e58f30b199366294af879e8597
test "$(pkg-config --variable=miem_revision musica-fortran)" = \
  9fdf14a189262eecb677862d877ab72b06c95e21
test "$(pkg-config --variable=mechanism_configuration_revision musica-fortran)" = \
  82c159ae6d74934318ffd6c405a45c2159065b12
test "$(pkg-config --variable=tuvx_revision musica-fortran)" = \
  bbf7dd9a144fa0f0294b3779f3f993818638e20c
test "$(pkg-config --variable=miem_enabled musica-fortran)" = ON
test "$(pkg-config --variable=tuvx_enabled musica-fortran)" = ON
pkg-config --variable=fortran_compiler_id musica-fortran
pkg-config --variable=fortran_compiler_version musica-fortran
pkg-config --libs musica-fortran
```

The reported Fortran compiler must match the compiler that will build
CheMPAS-A. The library list is the complete static link closure; do not append a
hard-coded `-lstdc++` or `-lc++`.

## 3.7 Ubuntu with GCC and Open MPI

The qualified MVP build used GNU Fortran 15.2.0, Open MPI 5.0.10, NetCDF-C
4.10.1, NetCDF-Fortran 4.6.3, PnetCDF 1.14.1, and PIO 2.6.9. Create one
conda environment so the compiler, MPI wrappers, and I/O libraries share an
ABI:

```bash
conda create -n chempas-a -c conda-forge \
  gcc=15.2 gxx=15.2 gfortran=15.2 openmpi=5.0.10 \
  libnetcdf=4.10.1 netcdf-fortran=4.6.3 libpnetcdf=1.14.1 \
  cmake pkg-config make git
conda activate chempas-a

export CHEMPAS_DEPS="$HOME/software/chempas-a/ubuntu-gnu"
export NETCDF="$CONDA_PREFIX"
export NETCDFF="$CONDA_PREFIX"
export PNETCDF="$CONDA_PREFIX"
export PIO="$CHEMPAS_DEPS/pio-2.6.9"
export MUSICA_PREFIX="$CHEMPAS_DEPS/musica-$MUSICA_REV"
export CHEMPAS_MAKE_TARGET=gfortran
```

Build PIO with the same wrappers:

```bash
git clone --depth 1 --branch pio2_6_9 \
  https://github.com/NCAR/ParallelIO.git ParallelIO-2.6.9
cmake -S ParallelIO-2.6.9 -B ParallelIO-2.6.9/build-chempas \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PIO" \
  -DCMAKE_C_COMPILER=mpicc \
  -DCMAKE_Fortran_COMPILER=mpifort \
  -DPIO_ENABLE_TIMING=OFF \
  -DPIO_ENABLE_TESTS=OFF
cmake --build ParallelIO-2.6.9/build-chempas --parallel 8
cmake --install ParallelIO-2.6.9/build-chempas
```

Configure and install MUSICA:

```bash
cmake -S MUSICA-CheMPAS-A -B MUSICA-CheMPAS-A/build-ubuntu \
  -DFETCHCONTENT_TRY_FIND_PACKAGE_MODE=NEVER \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$MUSICA_PREFIX" \
  -DCMAKE_C_COMPILER=mpicc \
  -DCMAKE_CXX_COMPILER=mpicxx \
  -DCMAKE_Fortran_COMPILER=mpifort \
  -DBUILD_SHARED_LIBS=OFF \
  -DBUILD_TESTING=OFF \
  -DMUSICA_BUILD_FORTRAN_INTERFACE=ON \
  -DMUSICA_ENABLE_MPI=ON \
  -DMUSICA_ENABLE_MICM=ON \
  -DMUSICA_ENABLE_MIEM=ON \
  -DMUSICA_ENABLE_TUVX=ON \
  -DMUSICA_ENABLE_CARMA=OFF \
  -DMUSICA_ENABLE_MIAM=OFF \
  -DMUSICA_USE_FMT=OFF
cmake --build MUSICA-CheMPAS-A/build-ubuntu --parallel 8
cmake --install MUSICA-CheMPAS-A/build-ubuntu
```

## 3.8 macOS with LLVM flang

Install the C/C++ compilers, flang, MPI, NetCDF-C, and build tools:

```bash
brew install llvm flang open-mpi netcdf cmake pkg-config autoconf automake libtool

export CHEMPAS_DEPS="$HOME/software/chempas-a/macos-llvm"
export NETCDF="$(brew --prefix netcdf)"
export NETCDFF="$CHEMPAS_DEPS/netcdf-fortran-4.6.2"
export PNETCDF="$CHEMPAS_DEPS/pnetcdf-1.14.1"
export PIO="$CHEMPAS_DEPS/pio-2.6.9"
export MUSICA_PREFIX="$CHEMPAS_DEPS/musica-$MUSICA_REV"
export CHEMPAS_MAKE_TARGET=llvm
export OMPI_CC=clang
export OMPI_CXX=clang++
export OMPI_FC=flang
```

Homebrew's Open MPI and NetCDF-Fortran modules are normally produced by
gfortran. They cannot be consumed as Fortran modules by flang. Build a static
NetCDF-Fortran 4.6.2 with flang against Homebrew NetCDF-C:

```bash
curl -L https://github.com/Unidata/netcdf-fortran/archive/refs/tags/v4.6.2.tar.gz \
  -o netcdf-fortran-4.6.2.tar.gz
tar -xf netcdf-fortran-4.6.2.tar.gz
mkdir -p netcdf-fortran-build
cd netcdf-fortran-build
CC=clang FC=flang \
CPPFLAGS="-I$NETCDF/include" LDFLAGS="-L$NETCDF/lib" \
PKG_CONFIG_PATH="$NETCDF/lib/pkgconfig" \
  ../netcdf-fortran-4.6.2/configure \
    --prefix="$NETCDFF" --disable-shared --enable-static
make -j8
make install
cd ..
```

Build PnetCDF without its gfortran-dependent Fortran interface. CheMPAS-A uses
PnetCDF through PIO's C interface on this platform:

```bash
curl -L https://parallel-netcdf.github.io/Release/pnetcdf-1.14.1.tar.gz \
  -o pnetcdf-1.14.1.tar.gz
tar -xf pnetcdf-1.14.1.tar.gz
cd pnetcdf-1.14.1
CC=clang MPICC=mpicc ./configure --prefix="$PNETCDF" \
  --disable-cxx --disable-fortran --disable-shared
make -j8
make install
cd ..

export PATH="$PNETCDF/bin:$PATH"
export PKG_CONFIG_PATH="$NETCDFF/lib/pkgconfig:$NETCDF/lib/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
test "$(pnetcdf-config --prefix)" = "$PNETCDF"
test "$(pkg-config --modversion netcdf-fortran)" = 4.6.2
```

Build PIO through the Open MPI wrappers selected by `OMPI_CC=clang` and
`OMPI_FC=flang`. PIO detects LLVM flang and uses `mpif.h` instead of the
incompatible Homebrew `mpi.mod`:

```bash
git clone --depth 1 --branch pio2_6_9 \
  https://github.com/NCAR/ParallelIO.git ParallelIO-2.6.9
cmake -S ParallelIO-2.6.9 -B ParallelIO-2.6.9/build-chempas-llvm \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PIO" \
  -DCMAKE_C_COMPILER=mpicc \
  -DCMAKE_Fortran_COMPILER=mpifort \
  -DPIO_ENABLE_TIMING=OFF \
  -DPIO_ENABLE_TESTS=OFF
cmake --build ParallelIO-2.6.9/build-chempas-llvm --parallel 8
cmake --install ParallelIO-2.6.9/build-chempas-llvm
```

Put the flang-built NetCDF-Fortran metadata before Homebrew paths, then build
MUSICA with direct compilers. MUSICA is rank-local in CheMPAS-A on macOS, so
its own MPI option is disabled; the MPAS executable itself remains MPI-enabled.

```bash
cmake -S MUSICA-CheMPAS-A -B MUSICA-CheMPAS-A/build-macos-llvm \
  -DFETCHCONTENT_TRY_FIND_PACKAGE_MODE=NEVER \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$MUSICA_PREFIX" \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_Fortran_COMPILER=flang \
  -DBUILD_SHARED_LIBS=OFF \
  -DBUILD_TESTING=OFF \
  -DMUSICA_BUILD_FORTRAN_INTERFACE=ON \
  -DMUSICA_ENABLE_MPI=OFF \
  -DMUSICA_ENABLE_MICM=ON \
  -DMUSICA_ENABLE_MIEM=ON \
  -DMUSICA_ENABLE_TUVX=ON \
  -DMUSICA_ENABLE_CARMA=OFF \
  -DMUSICA_ENABLE_MIAM=OFF \
  -DMUSICA_USE_FMT=OFF
cmake --build MUSICA-CheMPAS-A/build-macos-llvm --parallel 8
cmake --install MUSICA-CheMPAS-A/build-macos-llvm
```

## 3.9 Derecho with the Cray Programming Environment

Build on a compute node, not a shared login node. This recipe pins
[`ncarenv/25.10`](https://arc.ucar.edu/articles/1006), the NSF NCAR default
stack since 3 March 2026; using the named stack makes the compiler-dependent
NetCDF, PnetCDF, and PIO modules resolve together. Start an
[interactive development job](https://ncar-hpc-docs.readthedocs.io/en/latest/pbs/),
replacing `YOUR_PROJECT_CODE`:

```bash
export PROJECT_CODE=YOUR_PROJECT_CODE
qinteractive -A "$PROJECT_CODE" -l walltime=02:00:00

module --force purge
module load ncarenv/25.10
module reset
module swap intel cce
module load cmake netcdf parallel-netcdf
module -t list

command -v cc CC ftn cmake pkg-config nc-config nf-config pnetcdf-config

export NETCDF="$(nc-config --prefix)"
export NETCDFF="$(nf-config --prefix)"
export PNETCDF="$(pnetcdf-config --prefix)"
export CHEMPAS_DEPS="/glade/work/$USER/chempas-a/ncarenv-25.10-cce"
export PIO="$CHEMPAS_DEPS/pio-2.6.9"
export MUSICA_PREFIX="$CHEMPAS_DEPS/musica-$MUSICA_REV"
export CHEMPAS_MAKE_TARGET=cray
```

Build the reference PIO release with the same Cray wrappers and I/O modules:

```bash
git clone --depth 1 --branch pio2_6_9 \
  https://github.com/NCAR/ParallelIO.git ParallelIO-2.6.9
cmake -S ParallelIO-2.6.9 -B ParallelIO-2.6.9/build-derecho-cce \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PIO" \
  -DCMAKE_C_COMPILER=cc \
  -DCMAKE_Fortran_COMPILER=ftn \
  -DPIO_ENABLE_TIMING=OFF \
  -DPIO_ENABLE_TESTS=OFF
cmake --build ParallelIO-2.6.9/build-derecho-cce --parallel 8
cmake --install ParallelIO-2.6.9/build-derecho-cce
```

Do not load Derecho's `musica/0.10.1` module: it does not satisfy the CheMPAS-A
version, revision, or MIEM API requirements. Build the pinned package with the
Cray compiler wrappers:

```bash
cmake -S MUSICA-CheMPAS-A -B MUSICA-CheMPAS-A/build-derecho-cce \
  -DFETCHCONTENT_TRY_FIND_PACKAGE_MODE=NEVER \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$MUSICA_PREFIX" \
  -DCMAKE_C_COMPILER=cc \
  -DCMAKE_CXX_COMPILER=CC \
  -DCMAKE_Fortran_COMPILER=ftn \
  -DBUILD_SHARED_LIBS=OFF \
  -DBUILD_TESTING=OFF \
  -DMUSICA_BUILD_FORTRAN_INTERFACE=ON \
  -DMUSICA_ENABLE_MPI=ON \
  -DMUSICA_ENABLE_MICM=ON \
  -DMUSICA_ENABLE_MIEM=ON \
  -DMUSICA_ENABLE_TUVX=ON \
  -DMUSICA_ENABLE_CARMA=OFF \
  -DMUSICA_ENABLE_MIAM=OFF \
  -DMUSICA_USE_FMT=OFF
cmake --build MUSICA-CheMPAS-A/build-derecho-cce --parallel 8
cmake --install MUSICA-CheMPAS-A/build-derecho-cce
```

Use the same `module` commands in later PBS run scripts. Changing the compiler
or `ncarenv` stack after compilation can select incompatible MPI and I/O
libraries. For current module and compiler guidance, see the
[NSF NCAR Derecho compiler documentation](https://ncar-hpc-docs.readthedocs.io/en/latest/compute-systems/derecho/compiling-code-on-derecho/).

## 3.10 Build CheMPAS-A and Verify the MUSICA Link

After completing one platform section and the MUSICA metadata checks in
Section 3.6, build the public MVP from its immutable tag:

```bash
git clone --branch v2026.08.01-rc2 --depth 1 \
  https://github.com/NCAR/CheMPAS-A.git
cd CheMPAS-A

set -o pipefail
make clean CORE=init_atmosphere
make -j8 "$CHEMPAS_MAKE_TARGET" CORE=init_atmosphere OPENMP=false \
  PIO="$PIO" NETCDF="$NETCDF" NETCDFF="$NETCDFF" PNETCDF="$PNETCDF" \
  PRECISION=double 2>&1 | tee build-init_atmosphere.log

make clean CORE=atmosphere
make -j8 "$CHEMPAS_MAKE_TARGET" CORE=atmosphere OPENMP=false \
  PIO="$PIO" NETCDF="$NETCDF" NETCDFF="$NETCDFF" PNETCDF="$PNETCDF" \
  PRECISION=double MUSICA=true 2>&1 | tee build-atmosphere.log
```

The Makefile performs a constructor-level MICM+MIEM link probe using only the
installed `musica-fortran.pc` flags before it links MPAS. Confirm both the
probe and final link message, then check the executables:

```bash
grep -F "Built a simple test program with MUSICA-Fortran version 0.16.5" \
  build-atmosphere.log
grep -F "MPAS was linked with the MUSICA-Fortran library version 0.16.5" \
  build-atmosphere.log
test -x init_atmosphere_model
test -x build_tables
test -x atmosphere_model
```

These checks work for the documented static MUSICA build; tools such as `ldd`
or `otool -L` will not list static archives. Without `MUSICA=true`, the
chemistry hooks compile out and the chemistry namelist records are ignored at
runtime.

For the runtime features enabled by this build, see
[Chapter 7](07-runtime-tracers.md) and
[Chapter 8](08-chemistry-coupling.md).

## 3.11 Cleaning

To remove all files that were created when the model was built, including the model executable itself, make may be run for the `clean` target:

```
make clean
```

As with compiling, the core to be cleaned is specified by the `CORE` environment variable, or by specifying a core explicitly on the command-line with `CORE=`.
