# MIEM Distributed-I/O and Scalability Design

**Status:** Implemented, benchmarked, clean-gate verified, and phase-checkpoint remote-verified

This document is the implementation contract for the scalability work in
`docs/chempas/mvp/PLAN_EMISSIONS.md`. It extends the exact-grid Phase 1 workflow; it does not
weaken inventory validation or introduce runtime horizontal regridding.

## Selected-cell API

MIEM will add a public `CellSelection` value with these semantics:

- global cell IDs are one-based inventory slots and must be unique;
- output cell `i` corresponds to input selection element `i`, so host order is
  preserved even when IDs are not sorted;
- an empty selection is the backward-compatible full-grid request;
- every ID must be in `1..global_n_cells`; and
- `global_n_cells` remains distinct from the selected/local cell count.

The C++ builder API is:

```cpp
miem::EmissionsBuilder()
  .SetGridDimensions(global_n_cells, n_vert_levels)
  .SetCellSelection(selected_global_cell_ids)
  .SetDiagnosticSelection(diagnostics)
  .AddSource(source)
  .Build();
```

MUSICA will carry the same contract through C and Fortran. The Fortran
constructor overload accepts `selected_global_cell_ids(:)`, while the existing
three-argument grid constructor continues to request the full grid. An
`emissions_t` reports both global and selected cell counts. Surface, layered,
sector, and category buffers use selected-host order.

CheMPAS-A passes owned `indexToCellID(1:nCellsSolve)` at construction. It no
longer constructs a global MIEM state or gathers fluxes by global index after
`run`; MIEM directly returns `nCellsSolve` values in the requested order.

## Rank-local NetCDF I/O

UPTEMPO and ECCAD readers receive the immutable selection. Each reader sorts a
temporary `(global ID, output position)` index, coalesces consecutive IDs into
maximal runs, reads only those runs with `nc_get_vara`, and scatters each run
back into host order. It never allocates an inventory-sized flux buffer in
selected mode.

The two time brackets are cached as selected-cell arrays. A bracket reload
therefore has memory complexity
`O(2 * selected_cells * inventory_species)` per source and rank. Each MPI rank
opens and reads its own selected hyperslabs; MIEM performs no MPI calls and
does not assume a particular decomposition. NetCDF failures remain rank-local
fatal errors handled by the existing CheMPAS chemistry error path.

The full-grid constructor remains available for compatibility and for a direct
distributed-versus-replicated equivalence test. Phase 7 acceptance requires
bitwise-equal selected fluxes for the same global IDs, time, species mapping,
hierarchy, and source configuration.

## Inventory grid metadata

MIEM exposes immutable `InventoryGridMetadata` after the first file is opened:

- global cell count and selected one-based global IDs;
- geometry class (`spherical` or `planar`);
- `on_a_sphere`, `is_periodic`, and optional `sphere_radius`;
- `chempas-mesh-sha256-v1` algorithm, digest, and field manifest; and
- selected `areaCell` plus every present cell-center coordinate among
  `latCell`, `lonCell`, `xCell`, `yCell`, and `zCell`, including units.

All configured sources must report identical metadata. Selected mode rejects
an inventory that lacks the exact-grid identity fields. MUSICA exposes the
metadata arrays without changing their order. Before applying the first
source, CheMPAS-A compares metadata global IDs, geometry class, area, and all
geometry-required coordinates against its owned MPAS mesh arrays. A mismatch
is fatal before MICM state mutation. The standalone SHA-256 validator remains
the prelaunch gate; runtime array comparison is an independent defense against
staging the wrong file after validation.

## Vertical sources

The mechanism-configuration extension is intentionally explicit:

```yaml
vertical injection: profile
vertical profile: [0.0, 0.25, 0.75]
```

`surface` is equivalent to `[1, 0, ...]`. A profile is source-specific,
dimensionless, fixed during a run, and interpreted from MPAS level 1 upward.
MIEM requires exactly `n_vert_levels` finite nonnegative entries whose sum is
one within a documented floating-point tolerance. This supports elevated and
vertically distributed sources without inventing plume-rise meteorology.

MIEM returns `layer_flux(species, level, selected_cell)` in
`kg m-2 s-1`; summing levels reproduces the source's vertically integrated
flux. Hierarchy selection is performed per source/species/cell before its
chosen profile is applied, so competing sources cannot be mixed across levels.
CheMPAS-A converts each layer independently:

```text
EMIS.s(k,i) = layer_flux(s,k,i) / (layer_depth(k,i) * molar_mass(s))
```

Direct surface diagnostics remain the column-integrated flux. Requested
layered diagnostics use `emis_<species>_layer` and are opt-in because their
storage scales with the MPAS column depth.

## Bounded sector and category diagnostics

Diagnostic allocation is controlled by a `DiagnosticSelection` containing
explicit sector names, category IDs, a layered-output flag, and a hard
`max_fields` limit. An empty selection allocates no disaggregated fields.
Unknown labels, duplicate labels, and a selection whose
`species * groups * (levels when layered)` count exceeds `max_fields` are
initialization errors.

MIEM aggregates only requested groups. MUSICA exposes the selected group names
and buffers. CheMPAS-A registers names derived from the same MIEM configuration
before stream setup:

```text
emis_<species>__sector_<sanitized-sector>
emis_<species>__category_<integer>
```

Sanitized labels must be unique. Totals retain the existing
`emis_<species>` names, and the checker verifies that selected category totals
sum to the total wherever all categories were requested.

## Native regridding decision

Phase 7 keeps `regridding: none` as the only accepted runtime setting. Native
regridding is not selected because the following contract is not yet available
in MIEM:

1. source and destination cell bounds/areas with an auditable CRS;
2. immutable sparse weights with a recorded generator, method, normalization,
   and hash;
3. a mass-conservation tolerance over masked and fractional cells;
4. deterministic ownership of destination rows across MPI ranks;
5. collective/parallel-NetCDF behavior that cannot deadlock the host's
   rank-local chemistry failure path; and
6. reproducible equivalence to the existing external conservative remapping
   workflow.

Any future native implementation must satisfy those conditions in a separate
plan and may not silently fall back to interpolation. Selected-cell reads are
an I/O optimization on an already exact MPAS inventory, not regridding.

## Benchmark and acceptance matrix

The benchmark uses existing production MPAS assets without committing them:

| Class | Mesh | Cells | Geometry | 8-rank partition |
|---|---|---:|---|---|
| Regional | `supercell_init.nc` | 28,080 | planar | `supercell.graph.info.part.8` |
| Global | `x1.40962.init.nc` | 40,962 | spherical | `x1.40962.graph.info.part.8` |

For each mesh, tooling creates an external deterministic two-time, two-species
inventory and runs both full-grid and selected-cell modes. It records:

- construction/first-open wall time;
- warm per-step wall time over repeated interpolated samples;
- process peak resident memory;
- requested cells, coalesced hyperslabs, and NetCDF payload bytes;
- inventory, mesh, executable, dependency, and partition hashes; and
- bitwise full-grid/selected flux equivalence for every rank-owned global ID.

The gate requires schema-valid reports for both meshes, selected payload bytes
and state elements proportional to owned cells, no per-rank full-grid flux
allocation in selected mode, and no scientific regression. Timing is recorded
but is not a pass/fail threshold because shared-filesystem cache and load are
not controlled in developer runs.

### Recorded Phase 7 results

`scripts/benchmark_miem_scalability.sh` generated a deterministic exact-grid
inventory outside the repository run data, compiled the public-Fortran-API
harness, and ran full-grid and selected-cell modes with eight ranks and 12 warm
samples. Every rank-owned NO/NO2 flux stream was bitwise identical between
modes. The versioned reports and schema are in
[`benchmarks/`](benchmarks/README.md).

The table uses aggregate payload/state over all eight ranks and the maximum
rank time or resident-memory value. The payload is the exact count implied by
the reader contract: requested cells times eight bytes times four inventory
bracket fields plus the exact-grid metadata fields. Persistent state counts
the exposed surface/layer buffers, two-time/two-species bracket cache, grid
metadata, and global IDs.

| Mesh | Mode | Payload bytes | Persistent elements | Peak RSS KiB | First open s | Warm step s |
|---|---|---:|---:|---:|---:|---:|
| Regional 28,080×60 | Full | 19,768,320 | 30,101,760 | 178,004 | 0.064 | 0.0310 |
| Regional 28,080×60 | Selected | 2,471,040 | 3,762,720 | 56,572 | 0.032 | 0.00350 |
| Global 40,962×26 | Full | 28,837,248 | 21,627,936 | 133,760 | 0.051 | 0.0200 |
| Global 40,962×26 | Selected | 3,604,656 | 2,703,492 | 51,432 | 0.051 | 0.00208 |

Selected payload and persistent state are exactly `1/8` of replicated totals
in both cases because the eight selections cover the global grid exactly once;
each selected rank reports `object_cells == owned_cells`, never global
`nCells`. Timing and RSS are evidence, not portable performance thresholds.

## Delivery boundaries

The upstream changes are delivered as separately tested and pushed commits in
MechanismConfiguration, MIEM, and MUSICA. CheMPAS-A pins those exact revisions,
then receives the host integration, tests, benchmarks, and documentation in
focused pushed milestones. Phase 7 is complete only after clean dependency and
CheMPAS builds, the full R0-R6/E0/E12 gates, the new distributed/metadata/
vertical/diagnostic tests, both production-mesh benchmarks, and remote-SHA
verification all pass.
