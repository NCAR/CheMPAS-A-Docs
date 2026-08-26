# MVP Stage 3: Local and Integration Qualification

Stage 3 passed on implementation commit
`8a7a4cbcd5c45ef3bc70a905155cd50185bc6965`. The compact result is
[`stage3-local-qualification-audit.json`](stage3-local-qualification-audit.json).

## Coupled Tier C Box

The normal and strict-reference Tier C mechanisms were each integrated with
the eight prescribed photolysis rates and analytic NO, NO2, and CO sources.
Both solves converged with finite, nonnegative state, the NOy change matched
the integrated NO plus NO2 input, and daylight produced independent NO and O3
responses relative to the otherwise identical dark calculation.

The CO check distinguishes two different claims. The applied CO mass and its
carbon content close exactly at the source entry point. The reduced Tier C
mechanism intentionally sends oxidized CO and CH4 carbon to untracked terminal
CO2, so Stage 3 does not claim conservation of the active chemical carbon
pool.

## Eight-Rank Multi-Cell Case

The executable integration uses 64 cells, 60 model layers, eight MPI ranks,
and two three-second chemistry intervals. It combines:

- a mesh-matched cyclic monthly upper-O3 package;
- a separate CAMS-like anthropogenic source group;
- a separate FINN-like fire source group;
- explicit NO, NO2, and CO mappings; and
- all eight TUV-x/Tier C photolysis channels.

The provider accepts a mesh-specific, strictly increasing upper grid while the
TUV-x adapter still requires its first edge to match the model top. The frozen
production x1.40962 package remains on its reviewed 45--100 km grid; the local
fixture begins at the chem-box 50 km top and therefore exercises the same seam
contract on a different mesh.

For both normal and strict-reference runs, the checker independently
reconstructed every total, sector, and category source field from the two
inventories. Applied mass was 14.9247895252472 kg NO, 22.6258825397889 kg NO2,
and 59.6991581009889 kg CO. The normal NOy source-ledger relative residual was
`2.91e-17`; the strict-reference residual was `5.16e-12`. Every photolysis
field was finite and positive in daylight and showed a nonzero spatial
response to upper O3. All 15 transported Tier C fields remained finite and
nonnegative. The largest final normal/strict absolute difference across the
checked chemistry and photolysis fields was `1.59e-10`.

The hash-verified detailed report is external to Git at
`reports/mvp/8a7a4cbc/stage3-local-report.json` beneath the Stage 0 data root.
Its SHA-256 is
`c7f2d2b19cf0fe28cd60f8b8f23ce5ce7f8dd057debec8b7a91344c32c9c93cd`.

## Fail-Closed Matrix

The qualification explicitly rejects:

| Contract error | Evidence |
|---|---|
| Missing prescribed O3 field | Provider executable test |
| Wrong O3 or emission units | Provider and inventory preparation tests |
| Non-Gregorian calendar | Provider and eight-rank MIEM runtime tests |
| Insufficient source time coverage | Standalone and eight-rank MIEM tests |
| Cell count, identity, or mesh geometry mismatch | Provider, inventory, and eight-rank tests |
| Invalid vertical coordinate or density/column pair | Provider executable tests |
| CAMS open-burning plus FINN overlap | Frozen overlap-policy unit test |
| Negative undeclared surface source | Inventory preparation tests |

The initialization-order contract also verifies that MIEM, prescribed-field,
TUV-x, and rate-index validation all occur before the sole
`chemistry_seed_chem` call. Thus a configuration or input failure terminates
before the initial chemistry seed can mutate prognostic state. Step-time
chemistry remains transactional and restores the pre-step state on a failed
solve.

## Reproduction

```bash
conda run -n mpas bash scripts/test_mvp_tier_c_sources.sh

conda run -n mpas python -m unittest \
  tests.test_mvp_o3_climatology \
  tests.test_prepare_mvp_emissions \
  tests.test_mvp_local_harness \
  tests.test_miem_inventory

conda run -n mpas bash scripts/test_mvp_prescribed_fields.sh .
conda run -n mpas bash scripts/test_miem_failure_paths.sh .

conda run -n mpas bash scripts/test_mvp_local_integration.sh \
  --report "$CHEMPAS_EMISSIONS_DATA_ROOT/reports/mvp/8a7a4cbc/stage3-local-report.json"
```

The tested `atmosphere_model` was 14,165,560 bytes with SHA-256
`982e52f803ddb0fc6175a80ac340856f3932acf02dcb320b5b7597ee4587c42a`.
