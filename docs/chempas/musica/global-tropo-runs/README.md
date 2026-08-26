# Verified global tropospheric NOx evidence

This directory is the portable, hash-closed evidence package for the completed
x1.40962 CAMS-GLOB-ANT v6.2 NO/NO2 experiment. All eleven promotion gates
passed. The reduced tier qualifies MIEM coupling and NOx-O3 source response;
the expanded tier qualifies the response of the experimental
Ox-HOx-NOx-CO-CH4 mechanism. Neither tier is a production air-quality model.

## Provenance and acceptance

- Science commit: `caa0c12dde7b862ce14a49021e25a45cc00b337f`
- `atmosphere_model` SHA-256:
  `ff7166f119c407a18108ce7b6171f7a53a44ef3e6cfc75f6f31550d6a3d131c2`
- CAMS science-inventory SHA-256:
  `d213866000e8a633954d0c730ba5524f729f26a97d02cc5a13d8b405aa6c8e9c`
- Expanded FS restart SHA-256:
  `5cc5c7bd7fb47631ca89dae025b8646222b95422b65e7739047bd890ece9f940`
- Diagnostic tropopause: layer-center pressure at least 150 hPa. Chemistry is
  still active above this diagnostic boundary.

| Tier | Gate receipts | Result |
|---|---|---|
| Reduced | R0, R-CAL, R1, R2, R3 | All passed and promotable |
| Expanded | F0, F-CAL, F1, FS, F2, F3 | All passed and promotable |

R3 passed 45 assertions and F3 passed 46. These include source and family
budgets, exact-grid lifecycle, restart equivalence, paired emissions-withheld
branches, day/night photolysis and radical behavior, finite/nonnegative state,
zero negative-clipping/solver rejection, lightning disabled, output cadence,
resource limits, and same-commit provenance.

## Temporal and branch semantics

The geographic source and column panels are final-time instantaneous fields at
the valid timestamps printed in their subtitles; they are not daily means. The
burden panels show hourly instantaneous states, while emitted-family and
closure curves are cumulative over their stated 24-hour intervals.

The machine-readable variant name `no_miem_control` is retained in reports and
schemas, but `control` is not an adequate scientific label for these states.
R3 begins from nonzero atmospheric NOx and compares CAMS-NOx emissions applied
with emissions withheld during the R3 analysis interval. All F3 variants
inherit the same FS restart after a 24-hour spin-up with CAMS-NOx emissions; F3
compares emissions continued with emissions withheld only during the subsequent
analysis day. Thus the differences quantify the marginal effect of applying or
continuing emissions over the analysis interval, not an emitting atmosphere
versus a pristine or never-emitted atmosphere.

## Budget results

The inventory retains its explicit molecular speciation: the R3 24-hour
integrated source was 93.243% NO and 6.757% NO2 by molecules. It injected
0.09489 Tg N over the day, equivalent to 34.6 Tg N yr-1 if that July day were
repeated. No synthetic 90/10 split was applied.

| Gate/family | Emitted | Emissions-minus-withheld burden | Residual | Allowed residual |
|---|---:|---:|---:|---:|
| R3 NOx | 6.774776721 Gmol | 6.774776720 Gmol | -0.5733 mol | 338,739 mol |
| R3 Ox | 0.457755184 Gmol | 0.457755184 Gmol | +0.01627 mol | 22,887.8 mol |
| F3 NOy | 6.772250150 Gmol | 6.772250150 Gmol | -0.1771 mol | 338,613 mol |

The residuals are many orders of magnitude below the declared tolerances. The
slight R3/F3 source-total difference reflects the consecutive 1 July and 2 July
inventory sampling periods, not a speciation change.

## Physical and chemical range audit

`concentration-audit.json` independently recomputes dry-air molar mixing ratios,
radical number densities, pressure-band weights, atmospheric mass, and selected
emissions-minus-withheld differences from the four hash-verified final
histories. All 70/70 hard physical bounds and 44/44 broad reference-screening
checks pass.

Final expanded emissions-continued-state lower-tropospheric statistics
(pressure at least 500 hPa) are:

| Quantity | Weighted mean | Weighted p99 | Exact maximum |
|---|---:|---:|---:|
| NO | 0.0216 ppb | 0.0968 ppb | 115.8 ppb |
| NO2 | 0.1419 ppb | 0.9597 ppb | 45.9 ppb |
| O3 | 42.95 ppb | 60.69 ppb | 89.24 ppb |
| HNO3 | 0.5809 ppb | 3.348 ppb | 26.60 ppb |
| CH4 | 1.896 ppm | 1.900 ppm | 1.900 ppm |
| CO | 87.67 ppb | 114.7 ppb | 118.9 ppb |
| H2O2 | 0.7868 ppb | 1.626 ppb | 1.975 ppb |
| CH2O | 0.2704 ppb | 0.6230 ppb | 1.435 ppb |
| CH3OOH | 0.6214 ppb | 1.913 ppb | 2.532 ppb |
| H2O | 0.8094% | 2.759% | 3.494% |

Across the complete pressure-at-least-150-hPa diagnostic domain, expanded OH
has a volume-weighted mean of 1.326 million molecule cm-3, p99 of 8.657 million
molecule cm-3, and maximum of 34.16 million molecule cm-3. The OH mean
difference is +0.47% for emissions continued minus emissions withheld. This is
near, and slightly above the upper end of, the audit's cited global-model
anchor; it passes the intentionally broad plausibility envelope but is not an
observational evaluation.

The lower-tropospheric expanded emissions-continued-minus-withheld differences
are +0.0121 ppb NO, +0.0436 ppb NO2, +0.0510 ppb O3, and +0.0209 ppb HNO3.
The reduced emissions-applied-minus-withheld difference instead gives -0.0544
ppb lower-tropospheric O3, consistent with the expected NO titration boundary
of its Leighton-only chemistry. The sign difference is a useful mechanism
diagnostic, not a claim about climatological ozone effects.

The reconstructed mesh area is 5.1010e14 m2 and dry-air mass is 5.1112e18 kg,
giving a 98,263 Pa hydrostatic-equivalent mean surface pressure. Pressure,
density, water, major species, and every chemistry tracer remain finite and
physical. Isolated NO/NO2 source-grid maxima are much larger than the weighted
p99 values but remain within the declared hard bounds.

Expanded O3 from 150--500 hPa has a weighted mean of 102.8 ppb. Above 150 hPa,
its weighted mean is 2.095 ppm and p99 is 5.974 ppm. That stratospheric-like
background is reported rather than hidden, but the mechanism is explicitly
unqualified there because it omits stratospheric chemistry.

## Restart qualification note

The immutable FS state at `2024-07-02_00:00:00` initialized every F2/F3
variant. In the science-commit runner, the staged 00Z input symlink in
`split_first` also matched the restart-output filename pattern. During F3, that
one run-local symlink was removed after `split_first` started so output
discovery selected the regular generated 12Z boundary restart. The registered
source file, its hash, and all initialized state were unchanged. The delivered
runner now ignores staged symlinks and requires the exact generated split
boundary, eliminating that operational workaround. Continuous/split state,
source, photolysis, and budget equivalence all passed.

## Resources

| Run | Wall time | Peak RSS | All-variant output |
|---|---:|---:|---:|
| R3 continuous | 934.8 s | 928,732 KiB | 12.23 GB |
| F3 continuous | 5,623 s | 1,365,004 KiB | 25.58 GB |

Full NetCDF histories, restarts, logs, and executable remain in the external
emissions-science data root. They are not duplicated in Git.

## Evidence map

- `evidence-publication-manifest.json` closes the hashes of eleven portable
  gate reports, two FS supporting receipts, their schemas, and the publisher.
- `r3-report.json` and `f3-report.json` contain the complete final acceptance
  assertions, budgets, diagnostics, file receipts, and resources.
- `concentration-audit.json` closes the physical/chemical statistics and its
  concentration-range PNG/PDF pair.
- `figure-manifest.json` closes eight 300-dpi PNG/PDF pairs, the four source
  histories, plotting protocol/code/style, schemas, and final reports. The
  primary science set now includes explicit emissions-branch and
  emissions-minus-withheld NO/NO2 diagnostic-tropospheric columns for both R3
  and F3.
- `figures/` contains nine raster/vector diagnostic pairs: eight from the main
  figure manifest plus the concentration-audit pair. Titles, UTC subtitles,
  panel labels, comparison semantics, and domains follow
  `chempas-science-plot-v1`.

Use `../GLOBAL_TROPOSPHERIC_NOX.md` for the exact preparation, promotion,
restart-registration, publication, plotting, and audit commands.

## Interpretation limits

This one-day experiment validates MIEM/global coupling, reduced NOx-O3 process
response, and the numerical behavior of the experimental expanded mechanism.
It does not validate regulatory air quality or a chemical climatology. Missing
capabilities include dry/wet deposition, detailed VOC and nighttime
NO3/N2O5 chemistry, soil/fire/biogenic sources, online plume rise, clouds in
the simplified photolysis treatment, chemical assimilation, multiweek spin-up,
and a unified troposphere-stratosphere mechanism.
