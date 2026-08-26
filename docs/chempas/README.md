# CheMPAS-A Developer Documentation

These pages describe the CheMPAS-A 26.08 MVP release candidate at
[`v2026.08.01-rc2`](https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01-rc2),
based on MPAS-Atmosphere v8.4.1. They complement the adapted
[MPAS-Atmosphere User's Guide](../users-guide/index.rst), the
[CheMPAS-A tutorial](../tutorial/index.rst), and the MPAS-Atmosphere
[Technical Description](../technical-description/index.rst).

## Start Here

- [MVP release-candidate guide](mvp/MVP_PRE_RELEASE.md) — demonstrated capability,
  reconstruction guidance, qualification evidence, and interpretation limits.
- [Architecture](architecture/ARCHITECTURE.md) — coupling boundaries and
  control flow.
- [MUSICA/MICM integration](musica/MUSICA_INTEGRATION.md) — chemistry state
  transfer and solver lifecycle.
- [MUSICA API reference](musica/MUSICA_API.md) — host-facing Fortran calls
  used by CheMPAS-A.
- [MIEM integration](musica/MIEM_INTEGRATION.md) — offline-emissions data
  contract, configuration, diagnostics, and validation.
- [Global NOx](musica/GLOBAL_TROPOSPHERIC_NOX.md) and
  [global methane](musica/GLOBAL_TROPOSPHERIC_METHANE.md) — promotion ladders
  for the global chemistry workflows.

## Supporting Material

The navigation includes the complete set of current CheMPAS-A Markdown
documents: component notes, TUV-x and LNOx guidance, scientific plotting
requirements, implementation records, every MVP qualification stage, and
the compact validation records used by the global workflows. JSON manifests
and audit records are retained beside the relevant pages as machine-readable
evidence but are not rendered as standalone documentation pages.

The public MVP repository contains the model implementation. Declarative
namelists, streams, mechanisms, and reconstruction instructions are published
in the [CheMPAS-A wiki](https://github.com/NCAR/CheMPAS-A/wiki). Commands in
implementation and qualification records that name development-only
`scripts/`, `test_cases/`, or `micm_configs/` paths are retained as provenance;
those automation trees are not part of the public MVP source distribution.

The comparison against MPAS-Model v8.3.1 is retained only as
[historical baseline context](upstream/2026-04-19-vs-mpas-v8.3.1.md); it does
not describe the current v8.4.1 source baseline.
