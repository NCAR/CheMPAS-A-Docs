# CheMPAS-A Developer Documentation

These pages describe the CheMPAS-A 26.08 MVP, released as
[`v2026.08.01`](https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01) and based on
MPAS-Atmosphere v8.4.1. They complement the adapted
[MPAS-Atmosphere User's Guide](../users-guide/index.rst), the
[CheMPAS-A tutorial](../tutorial/index.rst), and the MPAS-Atmosphere
[Technical Description](../technical-description/index.rst).

## Start Here

- [Architecture](architecture/ARCHITECTURE.md) — coupling boundaries and
  control flow.
- [MUSICA/MICM integration](musica/MUSICA_INTEGRATION.md) — chemistry state
  transfer and solver lifecycle.
- [MUSICA API reference](musica/MUSICA_API.md) — host-facing Fortran calls
  used by CheMPAS-A.
- [MIEM integration](musica/MIEM_INTEGRATION.md) — offline-emissions data
  contract, configuration, and diagnostics.
- [TUV-x photolysis](guides/TUVX_INTEGRATION.md) and
  [lightning NOx](guides/LNOX_INTEGRATION.md) — photolysis and lightning
  source configuration.
- [Visualization](guides/VISUALIZE.md) — plotting chemistry output.

## Source and Examples

The public release contains the model implementation, the ABBA, LNOx-O3, and
Chapman + NOx mechanisms, and a minimal container workflow for three example
cases. Declarative namelists, streams, mechanisms, and reconstruction
instructions for the other examples are published in the
[CheMPAS-A wiki](https://github.com/NCAR/CheMPAS-A/wiki). Some pages also
describe preprocessing and plotting tools that are maintained in the
development repository and are not part of the public release.
