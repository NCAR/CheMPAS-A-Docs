# Running the Examples with Docker

The [v2026.08.01 release](https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01) provides a minimal Docker build and run
workflow for
three bounded chemistry demonstrations:

- Supercell ABBA transport and chemistry (`supercell-abba`)
- Supercell lightning NOx, O3, and NO2 photolysis (`supercell-lnox`)
- Global Chapman chemistry with NOx and photolysis (`chapman-nox-global`)

The supported instructions build the image from the public source repository
and do not assume access to a prebuilt registry image.

The repository-local [Docker README](https://github.com/NCAR/CheMPAS-A/blob/v2026.08.01/docker/README.md)
is the command reference tied directly to the current implementation.

## Scope

The runtime image contains:

- `init_atmosphere_model` and the MUSICA-enabled `atmosphere_model`;
- the three case directories and their minimal stream lists;
- three NetCDF initializer scripts;
- six MICM and TUV-x configuration files;
- the MUSICA TUV-x data required by the cases; and
- a small Python environment containing Python 3.12, NumPy, and netCDF4.

It intentionally contains no plotting stack, development image target, full
script collection, CAMS/FINN preparation workflow, or production emissions
experiment. Analyze `output.nc` on the host with separately installed tools.

The runner always uses eight MPI ranks and NetCDF streams. The included
partitions and smoke-test checks are tested for that rank count; it is not
a user-selectable container option.

## Pinned chemistry stack

The container builds MUSICA-Fortran 0.16.5 from source revision
`1403e3d22717bc87f3bf9d0aa591caf039c92bbc`. That revision resolves the same
dependency closure documented in [Building CheMPAS-A](../users-guide/03-building.md):

| Component | Revision |
|---|---|
| MICM | `bb57684a2047f0e58f30b199366294af879e8597` |
| MIEM | `9fdf14a189262eecb677862d877ab72b06c95e21` |
| MechanismConfiguration | `82c159ae6d74934318ffd6c405a45c2159065b12` |
| TUV-x | `bbf7dd9a144fa0f0294b3779f3f993818638e20c` |

The image does not use an arbitrary MICM `main` checkout or a local development
branch.

## Host requirements

- Docker Engine or Docker Desktop with Linux/AMD64 support
- Enough resources for eight MPI ranks
- At least 1 GiB of container shared memory
- A writable host directory for downloaded input data and generated output

The supported image platform is `linux/amd64`. Docker Desktop can use x86-64
emulation on Apple Silicon, although the build and runs are slower than on a
native AMD64 host.

For `supercell-lnox`, allocate at least 8 GiB to the Docker Desktop virtual
machine. The bounded test run used approximately 6.8 GiB at peak;
smaller limits can terminate the model with exit status 137.

## Build the image

Clone the release and build the runtime target:

```bash
git clone --branch v2026.08.01 --depth 1 \
  https://github.com/NCAR/CheMPAS-A.git
cd CheMPAS-A

docker build --platform linux/amd64 \
  -f docker/Containerfile \
  --target run \
  -t chempas-a:docker .
```

The build compiles the MPAS initialization and atmosphere cores plus the
pinned dependency stack. Check the installed runner:

```bash
docker run --rm --platform linux/amd64 chempas-a:docker --help
```

Only the three case names listed at the top of this page should be shown.

## Create the data volume

Input data and outputs remain on the host rather than in the image:

```bash
mkdir -p "$HOME/Data/CheMPAS"
```

The examples below mount that directory at `/data/CheMPAS`. The runner
downloads missing NCAR MPAS v7.0 supercell and JW baroclinic-wave test data,
and keeps the extracted archives for subsequent runs.

## Run the three cases

Supercell ABBA:

```bash
docker run --rm \
  --platform linux/amd64 \
  --shm-size=1g \
  -v "$HOME/Data/CheMPAS:/data/CheMPAS" \
  chempas-a:docker supercell-abba
```

Supercell lightning NOx, O3, and NO2 photolysis:

```bash
docker run --rm \
  --platform linux/amd64 \
  --shm-size=1g \
  -v "$HOME/Data/CheMPAS:/data/CheMPAS" \
  chempas-a:docker supercell-lnox
```

Global Chapman chemistry with NOx:

```bash
docker run --rm \
  --platform linux/amd64 \
  --shm-size=1g \
  -v "$HOME/Data/CheMPAS:/data/CheMPAS" \
  chempas-a:docker chapman-nox-global
```

Do not omit `--shm-size=1g`. Docker's default 64 MiB shared-memory allocation
is insufficient for these eight-rank Open MPI runs and can cause a bus error
during initialization.

## Shorter test runs

Without an override, each supercell case runs for 2 hours and the global case
for 24 hours. Override the copied namelist duration with an environment
variable:

```bash
docker run --rm \
  --platform linux/amd64 \
  --shm-size=1g \
  -e CHEMPAS_RUN_DURATION=00:10:00 \
  -v "$HOME/Data/CheMPAS:/data/CheMPAS" \
  chempas-a:docker supercell-abba
```

Use `00:10:00` for each supercell case and `01:00:00` for the global
case. The global output stream is hourly, so a one-hour run is required to
produce both initial and final records for verification.

Additional runner options are:

| Option | Effect |
|---|---|
| `--setup-only` | Download, initialize, and stage the case without running the atmosphere core |
| `--no-download` | Fail instead of downloading a missing NCAR test-case archive |
| `--force-init` | Regenerate the initialization files, including the shared JW initial state used by the global case |

## Outputs and reruns

The host receives one run directory per case, plus shared `supercell/` and
`jw_baroclinic_wave/` directories that hold the extracted archives and the
generated initial states:

```text
$HOME/Data/CheMPAS/supercell_abba/
$HOME/Data/CheMPAS/supercell_lnox/
$HOME/Data/CheMPAS/chapman_nox_global/
```

Each contains `output.nc`, `run.out`, and MPAS logs. Before a rerun, the
runner moves those active outputs under `archive/<UTC-timestamp>/`; it does not
silently overwrite them.

After atmosphere integration, the runner requires:

- `output.nc` and `log.atmosphere.0000.out`;
- at least two output time records;
- `Critical error messages = 0`; and
- the expected chemistry fields with finite data.

| Case | Expected chemistry output |
|---|---|
| `supercell-abba` | `qA`, `qB`, `qAB` |
| `supercell-lnox` | `qNO`, `qNO2`, `qO3`, `j_jNO2` |
| `chapman-nox-global` | `qO2`, `qO3`, `qO`, `qNO`, `qNO2`, `j_jO2`, `j_jO3_O`, `j_jO3_O1D`, `j_jNO2` |

## Docker Compose

The source repository also provides `docker/compose.yaml`. It fixes the
platform and shared-memory allocation and mounts `$HOME/Data/CheMPAS`:

```bash
docker compose -f docker/compose.yaml build
docker compose -f docker/compose.yaml run --rm chempas supercell-abba
```

Replace the final case name with either of the other supported cases.

## Tested configuration

The v2026.08.01 runtime content (commit
`a76dd8ae2adce569c45433a53503a6f3c791f325`) was tested on Linux/AMD64
with eight MPI ranks. Every expected value in both output records was finite
and unmasked, and every rank-zero log reported zero critical errors.

| Case | Duration | Output size | Result |
|---|---:|---:|---|
| Supercell ABBA | 10 min | 365.2 MB | ABBA conversion and transport evolved from the initialized state |
| Supercell LNOx + O3 | 10 min | 392.1 MB | Coupling, TUV-x initialization, and execution passed |
| Global Chapman + NOx | 1 hour | 317.0 MB | Species and photolysis fields developed nonzero finite ranges |

Output sizes reflect the runner's minimal output lists; the wiki examples
write fuller lists.

The ten-minute LNOx test run did not trigger measurable NO or NO2
production, so it verifies container plumbing and coupling rather than a
lightning-source science signal. The release template also starts at
00:00 UTC, after local sunset at the fixed column, so `j_jNO2` stays near
zero. Use a suitably developed supercell and longer
run before interpreting LNOx production.

Docker Desktop may print PMIx topology warnings while the model continues.
The global case may also report IEEE underflow or denormal flags during normal
shutdown. Treat these as nonfatal only when the process exits successfully,
the runner completes its NetCDF checks, and the rank-zero log reports zero
critical errors.

## Reproducibility

Record the source commit used to build the image, the local image ID, Docker
platform and resource allocation, run command, mounted data root, and hashes
of the active case inputs and outputs. Continue with the full
[Reproducibility Checklist](https://github.com/NCAR/CheMPAS-A/wiki/Reproducibility-Checklist) before comparing or
interpreting scientific results.
