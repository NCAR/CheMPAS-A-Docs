# MIEM Scalability Benchmark Reports

These versioned reports are the Phase 7 production-mesh scalability evidence:

- `phase7-regional.json`: 28,080-cell planar supercell mesh, 60 levels;
- `phase7-global.json`: 40,962-cell spherical x1.40962 mesh, 26 levels; and
- `miem-scalability-report.schema.json`: report contract.

The production mesh/init files and eight-rank graph partitions are external
data and are not committed. The harness creates a temporary deterministic,
two-time, two-species source file and packages it as an exact-grid UPTEMPO
inventory with `scripts/prepare_miem_inventory.py`. It does not download data
or perform runtime regridding. The temporary source, packaged inventory,
configuration, executable, rank metrics, and flux streams are removed after a
successful run; their hashes and relevant dimensions remain in each report.

With the pinned MUSICA environment active, reproduce both reports with:

```bash
scripts/benchmark_miem_scalability.sh --case all --warm-steps 12
```

The defaults resolve these external assets under `$HOME/Data/CheMPAS`:

```text
supercell/supercell_init.nc
supercell/supercell.graph.info.part.8
jw_baroclinic_wave/x1.40962.init.nc
jw_baroclinic_wave/x1.40962.graph.info.part.8
```

Use the corresponding `--regional-mesh`, `--regional-partition`,
`--global-mesh`, and `--global-partition` options when they are staged
elsewhere. `--work-root` chooses a parent for the isolated workspace and
`--keep-work` retains successful raw artifacts for inspection.

For each rank, the full-grid and selected-cell runs serialize sample number,
global ID, NO flux, and NO2 flux as fixed-width binary records. Matching stream
size and SHA-256 proves bitwise equality at the first endpoint and every warm
interpolated time. Reader payload and hyperslab counts are derived from the
implemented coalesced-run contract; timing and Linux `VmHWM` are measured.
Only correctness and owned-cell scaling gate acceptance—timing is
informational because filesystem cache and host load are uncontrolled.
