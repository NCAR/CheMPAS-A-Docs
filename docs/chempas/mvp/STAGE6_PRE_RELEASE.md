# MVP Stage 6: Pre-Release Evidence

Stage 6 publishes the compact, reproducible evidence bundle for the passing M3
attribution experiment and closes the MVP documentation. The machine-readable
summary is [`stage6-evidence-audit.json`](stage6-evidence-audit.json), and the
new-user entry point is [`MVP_PRE_RELEASE.md`](MVP_PRE_RELEASE.md).

## Published Figure Bundle

All seven products follow `chempas-science-plot-v1`, have both a 300-dpi PNG
and vector PDF, and passed visual inspection:

| Figure | Quantity | Time Semantics |
|---|---|---|
| 01 | Spatial upper-atmosphere O3 climatology and overhead column | Instantaneous, 2024-07-01 12:00 UTC |
| 02 | CAMS anthropogenic and FINN fire NO/NO2/CO surface fluxes | Model-step time-weighted Daily Mean, 00:00--24:00 UTC |
| 03 | Absolute NO, NO2, CO, and O3 diagnostic-troposphere column burdens for all three surface-source scenarios | Trapezoidal time-weighted Daily Mean, 00:00--24:00 UTC |
| 04 | Anthropogenic and fire NO, NO2, CO, and O3 column contributions | Trapezoidal time-weighted Daily Mean, 00:00--24:00 UTC |
| 05 | Lowest-level `jNO2` and `jO3_O1D` day/night structure | Instantaneous, 12:00 and 00:00 UTC |
| 06 | Applied source mass histories, independent source closure, and NOy residual ratios | Accumulated sources and endpoint ledgers |
| 07 | Prognostic/prescribed O3 model-top profile stitch | Instantaneous, 2024-07-01 00:00 UTC |

The figure manifest SHA-256 is
`29e3bab6f860ae8c3ad34e7616f52b6242d841214242d9cb02eb6c271e564266`.
It closes the report, retained-history manifest, plotter, style module,
plotting protocol, schemas, individual image hashes, time-integration methods,
and visual attestation. The retained-history manifest SHA-256 is
`59d802276c17b9615d0894578303dac4c499706cea86bf241955a896918f9da2`.

The absolute and paired burden products explicitly contain NO and NO2 as well
as CO and O3. Public titles use Title Case, while subtitles carry the complete
UTC range, domain, comparison, and time semantics. Member and difference
labels use the physical source configuration rather than ambiguous status
terms.

## Evidence Closure

The figures derive from the passing M3 report with SHA-256
`931913f02d33cc14db1ede6a093140755c492e02686ccc2ea4718e3f294daae5`.
All 27 retained history files were size- and hash-checked before plotting. The
global ladder audit SHA-256 is
`2faccb96113ddbacf49fdbc0451ec590d0d135facc843a341d6f09980cc22faf`.

The tracked evidence bundle contains only compact JSON/Markdown provenance and
the selected PNG/PDF figures. Native provider files, prepared NetCDF packages,
the 27 histories, restarts, executable, and regression logs remain beneath
`CHEMPAS_EMISSIONS_DATA_ROOT` and are addressed by logical paths plus hashes.

## Documentation and Reproduction

[`MVP_PRE_RELEASE.md`](MVP_PRE_RELEASE.md) documents the accepted scope, build,
external-data layout, preparation/audit commands, M0--M3 execution, plot
generation, interpretation, limitations, and final checklist. The focused
plot workflow and exact Daily Mean definitions are in
[`VISUALIZE.md`](../guides/VISUALIZE.md#plot_global_mvppy).

Every tracked relative link in the MVP plan, MVP evidence documents, and the
updated visualization guide was resolved locally. All example paths match
tracked configuration or script locations; commands use placeholders only for
the explicitly external data and TUV-x roots.
