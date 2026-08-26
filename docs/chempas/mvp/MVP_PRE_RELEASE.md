# CheMPAS-A MVP Release Candidate

The CheMPAS-A Minimum Viable Product is a bounded global demonstration of
transported gas-phase chemistry, TUV-x photolysis, spatial monthly
upper-atmosphere O3, and independent anthropogenic and fire surface sources.
All required implementation stages, the M0--M3 global ladder, and the complete
repository regression suite passed.

This is a process-integration release candidate. It is not a production
air-quality forecast or a chemically equilibrated global-composition product.

## Demonstrated Configuration

- Reduced Ox-HOx-NOx-CO-CH4 gas-phase chemistry with 15 transported
  chemical species.
- Eight TUV-x photolysis channels driven by the prognostic model column and a
  cyclic monthly MERRA-2 O3 climatology strictly above the 45 km model top.
- Explicit CAMS-GLOB-ANT v6.2 anthropogenic NO, NO2, and CO, with the
  agricultural-waste-burning sector withheld from the harmonized inventory.
- Independent FINNv2.5.1 fire NO, NO2, and CO using the provider species
  directly and a documented daily-total timing approximation.
- Exact-grid x1.40962 input packages and eight-rank execution.
- A 24-hour attribution experiment spanning
  2024-07-01 00:00--2024-07-02 00:00 UTC.

The three attribution scenarios are:

| Scenario | Configuration |
|---|---|
| No Surface Emissions | No CAMS or FINN source group; lightning source rate is zero |
| Anthropogenic Emissions | Harmonized non-fire CAMS NO, NO2, and CO |
| Anthropogenic + Fire Emissions | The same CAMS sources plus FINN NO, NO2, and CO |

Anthropogenic Emissions minus No Surface Emissions is the Anthropogenic Source
Contribution. Anthropogenic + Fire Emissions minus Anthropogenic Emissions is
the Fire Source Contribution. No Surface Emissions is not a pristine
atmosphere: it begins from the same chemically populated initial state as the
other scenarios and undergoes the same transport, chemistry, and photolysis.
The paired differences isolate only the declared surface-source additions.

## Evidence Map

| Stage | Evidence |
|---|---|
| 0: Data and interfaces | [`STAGE0_DATA_CONTRACT.md`](STAGE0_DATA_CONTRACT.md) |
| 1: Prescribed upper O3 | [`STAGE1_PRESCRIBED_O3.md`](STAGE1_PRESCRIBED_O3.md) |
| 2: CO and source inventories | [`STAGE2_EMISSIONS.md`](STAGE2_EMISSIONS.md) |
| 3: Local qualification | [`STAGE3_LOCAL_QUALIFICATION.md`](STAGE3_LOCAL_QUALIFICATION.md) |
| 4: Global M0--M3 ladder | [`STAGE4_GLOBAL_LADDER.md`](STAGE4_GLOBAL_LADDER.md) |
| 5: Full regression | [`STAGE5_FULL_REGRESSION.md`](STAGE5_FULL_REGRESSION.md) |
| 6: Figures and documentation | [`STAGE6_PRE_RELEASE.md`](STAGE6_PRE_RELEASE.md) |

Each stage has a compact JSON audit beside its narrative. The scientific plots
are closed by [`figure-manifest.json`](figure-manifest.json), and every plotted
M3 history is closed by
[`m3-history-manifest.json`](m3-history-manifest.json).

The commands below preserve the development qualification workflow. The public
MVP repository does not ship that automation tree; public reconstruction uses
the declarative inputs and manual procedure in the
[Global Chemistry and Emissions](https://github.com/NCAR/CheMPAS-A/wiki/Global-Chemistry-and-Emissions)
wiki guide.

## Build

The accepted Linux build uses the pinned MUSICA-Fortran 0.16.5 closure with
GNU Fortran and double-precision MPAS reals. From a clean candidate tree:

```bash
conda activate mpas
scripts/check_build_env.sh
eval "$(scripts/check_build_env.sh --export)"

make -j8 gfortran \
  CORE=atmosphere PIO="$PIO" NETCDF="$NETCDF" PNETCDF="$PNETCDF" \
  PRECISION=double MUSICA=true
```

The Stage 5 candidate executable is 14,165,560 bytes with SHA-256
`0049e8968273f95ec7404a4c123fa514458b29681fd2c8f117634b78d4d0988a`.
See [`STAGE5_FULL_REGRESSION.md`](STAGE5_FULL_REGRESSION.md) for the exact
dependency revisions and complete test matrix.

## Data Preparation

The normative input inventory is
[`external-inputs.json`](../../_downloads/mvp/external-inputs.json).
It records logical paths, sizes, and SHA-256 values beneath one external data
root. Native provider data, conservative weights, prepared NetCDF packages,
model histories, restarts, executables, and logs are intentionally not stored
in Git.

```bash
export CHEMPAS_EMISSIONS_DATA_ROOT=/path/to/emissions-science
export CHEMPAS_TUVX_DATA=/path/to/MUSICA/configs/tuvx/data
```

Prepare or re-audit the exact-grid source packages:

```bash
conda run -n mpas python scripts/prepare_mvp_emissions.py all \
  --manifest test_cases/global_mvp/external-inputs.json

python scripts/prepare_mvp_o3_climatology.py verify \
  --package "$CHEMPAS_EMISSIONS_DATA_ROOT/prescribed/merra2-o3-v5.12.4-x1.40962/merra2-o3-monthly-climatology.x1.40962.nc" \
  --mesh "$CHEMPAS_EMISSIONS_DATA_ROOT/raw/mpas-x1.40962/x1.40962.static.nc"
```

The runner independently validates every staged file against the frozen
manifest. Preparation assumptions, including FINN local-date timing and the
CAMS/FINN overlap policy, are in the Stage 0 and Stage 2 evidence.

## Global Ladder

Run the gates in order. A later gate refuses promotion unless its predecessor
uses the same tracked commit, executable, and external-input manifest.

```bash
for gate in M0 M1 M2 M3; do
  conda run --no-capture-output -n mpas \
    scripts/run_global_mvp.sh \
      --gate "$gate" \
      --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
      --tuvx-data "$CHEMPAS_TUVX_DATA" \
      --executable ./atmosphere_model
done
```

M0 is a 15-minute normal/strict calibration, M1 is a one-hour combined-source
shakedown, M2 checks a continuous six-hour run against a 3+3-hour restart, and
M3 runs the complete three-scenario attribution day. All four gates passed on
implementation commit `9f703f505051b8eb3700e9ecae927fc1c84746ca`; their
report hashes and resource use are in the Stage 4 audit.

## Plot Reproduction and Time Semantics

Catalog the retained M3 histories, generate the seven PNG/PDF pairs, inspect
the PNGs, and only then record the visual attestation:

```bash
mvp_gate_commit=9f703f505051b8eb3700e9ecae927fc1c84746ca

python scripts/catalog_global_mvp_histories.py \
  --report "$CHEMPAS_EMISSIONS_DATA_ROOT/reports/global-mvp/$mvp_gate_commit/m3-report.json" \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --output docs/chempas/mvp/m3-history-manifest.json

python scripts/plot_global_mvp.py \
  --history-manifest docs/chempas/mvp/m3-history-manifest.json \
  --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
  --outdir docs/chempas/mvp/figures \
  --manifest docs/chempas/mvp/figure-manifest.json \
  --dpi 300

python scripts/plot_global_mvp.py \
  --attest-visual-inspection docs/chempas/mvp/figure-manifest.json
```

The NO, NO2, CO, and O3 absolute-column and paired-contribution figures are
Daily Means: they use trapezoidal time integration across all nine
instantaneous records from 00:00 through 24:00 UTC. The CAMS/FINN source-flux
figure is a model-step time-weighted Daily Mean using all 192 left-endpoint
450-second samples, matching source application. Upper O3, the day/night
photolysis maps, and the model-top stitch are explicitly Instantaneous. The
source-mass figure is accumulated over the day with endpoint ledger residuals.

The plotting protocol, exact titles/subtitles, and manifest workflow are also
documented in [`VISUALIZE.md`](../guides/VISUALIZE.md#plot_global_mvppy).

## Interpretation Limits

- The experiment is only 24 hours and has no chemical spin-up; it demonstrates
  immediate coupled process response, not equilibrium or forecast skill.
- The reduced mechanism deliberately omits detailed VOC chemistry and a
  comprehensive nighttime mechanism.
- Oxidized CO and CH4 carbon terminates in untracked CO2, so the evidence
  claims an input-carbon ledger, not closure of active chemical carbon.
- Fire is injected at the surface. There is no online plume rise.
- Wet deposition, dry deposition, SO2, sulfate aerosol, and aerosol-radiation
  interactions are deferred.
- Prescribed O3 above the model top is a photolysis input. It is not a surface
  source and does not modify prognostic model O3.
- FINN daily totals use the documented local-date-to-noon-UTC approximation;
  the product does not provide subdaily event timing.
- The results must not be presented as production air quality or a complete
  tropospheric chemistry simulation.

## Pre-Release Checklist

- M0--M3: pass and promotable.
- Full clean-tree regression: 268 Python tests and all 16 shell contracts pass.
- Three-scenario source mass, NOy ledgers, paired attribution, restart, MPI, finite
  state, and all eight photolysis channels: pass.
- Seven protocol-compliant, visually inspected PNG/PDF pairs: published.
- Exact input, executable, report, history, plot-code, and figure hashes:
  recorded.
- Large generated artifacts: retained only beneath the external data root.
