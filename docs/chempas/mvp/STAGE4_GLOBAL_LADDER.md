# MVP Stage 4: Global Promotion Ladder

Stage 4 passed on implementation commit
`9f703f505051b8eb3700e9ecae927fc1c84746ca`. M0, M1, M2, and M3 all used
the same x1.40962 inputs, eight-rank partition, executable, external-input
manifest, reduced mechanism, and eight-channel TUV-x configuration. The compact
result is [`stage4-global-ladder-audit.json`](stage4-global-ladder-audit.json).

## Promotion Results

| Gate | Simulated Interval | Runs | Assertions | Longest Run | Output | Result |
|---|---:|---:|---:|---:|---:|---|
| M0 | 15 minutes | Normal and strict reference | 10/10 | 924.19 s | 910,402,312 bytes | Pass, promotable |
| M1 | 1 hour | Anthropogenic + Fire Emissions | 10/10 | 202.14 s | 1,138,002,880 bytes | Pass, promotable |
| M2 | 6 hours | Continuous and 3+3-hour restart | 11/11 | 1,235.31 s | 4,019,276,800 bytes | Pass, promotable |
| M3 | 24 hours | All three surface-source scenarios | 14/14 | 5,565.0 s | 6,083,247,132 bytes | Pass, promotable |

The tested `atmosphere_model` SHA-256 was
`0049e8968273f95ec7404a4c123fa514458b29681fd2c8f117634b78d4d0988a`.
The report checker SHA-256 was
`96d15f25deffcf0e60f805d12c9580a3a4ff66576619a15214770222421c140a`.
Every run remained below its wall-time, peak-memory, and output-volume
envelope.

The four hash-verified reports remain outside Git under
`reports/global-mvp/9f703f505051b8eb3700e9ecae927fc1c84746ca` beneath the frozen data root.
Their SHA-256 values are recorded in the compact audit. M0--M2 histories were
pruned after promotion; the passing M3 histories are retained and cataloged by
[`m3-history-manifest.json`](m3-history-manifest.json).

## M3 Attribution

All three scenarios started from an identical atmospheric and photolysis state:

- No Surface Emissions;
- Anthropogenic Emissions; and
- Anthropogenic + Fire Emissions.

The reactive-nitrogen ledger closed independently for every scenario. The No
Surface Emissions residual was `0.0868893531 mol N` against an allowed
`0.3175935253 mol N`. The Anthropogenic Emissions and Anthropogenic + Fire
Emissions residuals were `-9.5367e-05` and `-9.9182e-05 mol N`, respectively.
The paired anthropogenic residual was `-0.0869846344 mol N` against an allowed
`331077.6119 mol N`; the paired fire residual was `-7.1526e-07 mol N` against
an allowed `105556.8248 mol N`.

The No Surface Emissions tolerance contains an explicit `5e-12` fraction of its
initial NOy burden in addition to the absolute tolerance. This recognizes
roundoff-scale drift in a `6.3318705061e10 mol N` transported background; it
does not grant a source allowance. A focused negative test confirms that a
one-mole ledger perturbation is rejected.

The checker also established:

- exact independent reconstruction of applied NO, NO2, and CO source mass;
- a carbon-input ledger for CO, with no claim that active reduced-mechanism
  carbon closes after oxidation to untracked terminal CO2;
- matched initial states across all three surface-source scenarios;
- nonzero anthropogenic and fire NO, NO2, CO, and O3 diagnostic-troposphere
  column responses;
- finite, nonnegative reduced-chemistry state in all scenarios; and
- complete spatial day/night behavior in all eight photolysis channels.

## Reproduction

Build from a clean tracked tree, set the frozen external roots, and execute the
gates in order. Each later gate refuses promotion unless its predecessor used
the same commit, executable, and external-input manifest.

```bash
export CHEMPAS_EMISSIONS_DATA_ROOT=/path/to/emissions-science
export CHEMPAS_TUVX_DATA=/path/to/MUSICA/configs/tuvx/data

for gate in M0 M1 M2 M3; do
  conda run --no-capture-output -n mpas \
    scripts/run_global_mvp.sh \
      --gate "$gate" \
      --data-root "$CHEMPAS_EMISSIONS_DATA_ROOT" \
      --tuvx-data "$CHEMPAS_TUVX_DATA" \
      --executable ./atmosphere_model
done
```

The runner validates all input sizes and hashes before staging, applies a disk
guard, writes run metadata, and invokes the closed report checker. Do not use
`--allow-dirty` or `--ignore-disk-guard` for a promotion run.
