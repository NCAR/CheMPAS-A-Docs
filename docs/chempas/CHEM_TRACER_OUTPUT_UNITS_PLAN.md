# Chemical tracer output units implementation plan and status

## Goal

Add output-only volume mixing ratio diagnostics for MICM chemical species while
preserving the existing dry-air mass mixing ratio fields as the authoritative
MPAS state. The existing `q<species>` fields remain unchanged for transport,
chemistry coupling, input, restart, and mass mixing ratio output.

Configured volume mixing ratio diagnostics use the name
`vmr_<MICM-species-name>` and are computed only immediately before history
output.

The existing MICM initial-concentration seeding behavior, including the special
ABBA case, is outside the scope of this work.

## Overall status

**Complete, integrated, and revalidated as of 2026-08-16.** The implementation
originated on `develop_units` and is now integrated with the current
`develop` chemistry, emissions, prescribed-field, and methane interfaces. The
transported and restarted chemistry state remains dry-air MMR; all VMR fields
are derived diagnostics populated only for output.

The principal development commits are:

| Commit | Description |
| --- | --- |
| `0f1eada4` | Document the chemical tracer output units plan. |
| `e661f738` | Implement configurable chemistry tracer output units. |
| `8a056e51` | Make the Python VMR checker use the same precomputed conversion factor as Fortran, including for subnormal values. |

### Development status

| Workstream | Status | Result |
| --- | --- | --- |
| Namelist contract | Complete | Added global `config_chem_tracer_output_unit` and per-species `config_chem_tracer_output_overrides`; default remains `mmr`. |
| MICM metadata discovery | Complete | Runtime discovery retains exact MICM names, MPAS source names, molar masses, and host-binding status. |
| Configuration validation | Complete | Global and override units, syntax, duplicates, exact species names, molar masses, name limits, and generated-name collisions are validated before integration. |
| Runtime diagnostics | Complete | Output-only `vmr_<species>` fields are registered in `diag`/`allFields`; authoritative `q<species>` fields remain in `state/scalars`. |
| Stream integration | Complete | VMR diagnostics are added to mutable history streams containing `scalars`; immutable input and restart streams are skipped. |
| Output conversion | Complete | Pre-output diagnostics use `q * CHEM_M_AIR / M_species * unit_scale` without changing, clipping, or feeding back into model state. |
| Host-bound species | Complete | Field-derived species use their MPAS host field (`H2O` from `qv`); fixed dry-air O2/N2 parameters use the same fixed fractions as the coupler rather than the `qv` index anchor. |
| User documentation | Complete | Chemistry coupling and namelist documentation describe syntax, units, precedence, naming, conversion, host binding, and restart behavior. |
| Test tooling | Complete | `scripts/check_chem_output.py` checks VMR relationships, metadata, forbidden variables/prefixes, and exact MMR reference comparisons. |

No ABBA-specific seeding logic was changed. Its eventual removal remains a
separate follow-up.

## Namelist interface

Add these options to the `&chemistry` record:

```fortran
config_chem_tracer_output_unit = 'mmr'
config_chem_tracer_output_overrides = ''
```

Accepted units are:

- `mmr`
- `fraction`
- `percent`
- `ppmv`
- `ppbv`
- `pptv`

Overrides use exact, case-sensitive MICM species names and take precedence over
the global setting:

```fortran
config_chem_tracer_output_overrides = 'O3=ppmv,NO=ppbv,NO2=ppbv'
```

Unit names are case-insensitive. An override of `species=mmr` suppresses the
volume mixing ratio companion for that species when the global selection is a
volume unit.

Initialization fails with a clear error for invalid units, malformed mappings,
unknown or duplicate species, non-positive molar masses, output-name
collisions, or names that exceed MPAS field-name limits.

## Naming and conversion

For MICM species `O3`:

| Selection | Output name | NetCDF units | Conversion from `qO3` |
| --- | --- | --- | --- |
| `mmr` | `qO3` | `kg kg^{-1}` | none |
| `fraction` | `vmr_O3` | `mol mol^{-1}` | `qO3 * M_air / M_O3` |
| `percent` | `vmr_O3` | `percent` | fraction `* 1e2` |
| `ppmv` | `vmr_O3` | `ppmv` | fraction `* 1e6` |
| `ppbv` | `vmr_O3` | `ppbv` | fraction `* 1e9` |
| `pptv` | `vmr_O3` | `pptv` | fraction `* 1e12` |

The conversion uses the existing dry-air molar mass constant
`CHEM_M_AIR = 0.0289644 kg mol^{-1}` and the species molar mass from the MICM
configuration.

## Implementation sequence

### 1. Add the configuration contract

Add the two namelist options to `src/core_atmosphere/Registry.xml` with `mmr`
and an empty override string as defaults. Regenerate the processed Registry,
Fortran includes, default namelist, and generated namelist documentation.

### 2. Preserve complete MICM species metadata

Extend lightweight MICM discovery in
`src/core_atmosphere/chemistry/musica/mpas_musica.F` to retain, for every MICM
species:

- the raw MICM name;
- the MPAS source field (`q<species>` or a host-bound field such as `qv`);
- the molar mass; and
- host-binding status.

Transport tracer creation remains unchanged and continues to inject only
non-host-bound `q<species>` constituents into `scalars`. Raw MICM names must not
be recovered by stripping a leading `q` from MPAS names.

### 3. Resolve output descriptors

During runtime variable preparation, parse the global unit and override map,
then cache an output descriptor for every species selecting a non-MMR unit.
Each descriptor records the source scalar, output name, molar mass, numeric
scale, units, and description.

Global selection applies to every MICM species, including host-bound `H2O`,
whose output is derived from MPAS `qv`. Mechanism-declared fixed dry-air O2
and N2 parameters retain their fixed coupler fractions as output metadata so
their VMR diagnostics are not incorrectly derived from the `qv` index anchor.

### 4. Register output-only runtime diagnostics

Extend the runtime diagnostic callback in
`src/core_atmosphere/mpas_atm_core_interface.F` to add one
`vmr_<species>` field per descriptor to `diag` and `allFields`.

The fields have dimensions `nVertLevels nCells`, one time level, and
unit-specific metadata. They are not members of `state/scalars` and therefore
are not transported or passed to MICM. Refactor the existing photolysis branch
so chemistry VMR diagnostics can be added when no photolysis fields exist.

### 5. Attach diagnostics to history streams

Before the first output, add configured VMR fields to mutable output streams
that already contain `scalars`, unless a field is already explicitly present.
Skip immutable input and restart streams. Explicit field names remain usable in
custom streams.

This makes VMR diagnostics additive history outputs while keeping restart files
MMR-only.

### 6. Convert immediately before output

Call a chemistry output routine from `atm_compute_output_diagnostics()` in
`src/core_atmosphere/mpas_atm_core.F`. For fields that will be written, the
routine reads the current source scalar and fills the corresponding diagnostic
using:

```text
vmr_output = q * CHEM_M_AIR / M_species * unit_scale
```

For a fixed dry-air host parameter, the corresponding fixed mole fraction is
multiplied only by `unit_scale`. The routine must not modify `scalars`,
tendencies, MICM state, or restart data, and must not add chemistry-specific
clipping.

### 7. Verify behavior

Extend `scripts/check_chem_output.py` with VMR relationship and metadata checks.
Cover:

1. Default `mmr` compatibility with no `vmr_*` fields and unchanged `q*`
   results.
2. A mixed-unit run that exercises `fraction`, `percent`, `ppmv`, `ppbv`,
   `pptv`, and an `mmr` override.
3. Element-wise conversion relationships and metadata.
4. Host-bound `H2O` derived from `qv`.
5. Restart output containing authoritative MMR state and no automatically
   attached VMR diagnostics.
6. Early failures for malformed or inconsistent configuration.
7. MUSICA-enabled compilation and an unaffected non-MUSICA build.

### 8. Document the feature

Update the chemistry user guide with the namelist syntax, precedence rules,
naming, formulas, host-bound species behavior, history/restart distinction, and
a mixed-unit example.

## Verification status

All planned build, runtime, failure-path, restart, metadata, and reference
comparisons passed. The original branch evidence is retained below, followed
by the current-stack integration evidence.

### Current-stack integration verification (2026-08-16)

| Check | Status | Evidence |
| --- | --- | --- |
| Clean supported build | Pass | Clean GFortran double-precision build linked with pinned MUSICA-Fortran 0.16.5 and MIEM support. |
| Python suite | Pass | All 268 discovered tests passed. |
| Maintained shell/runtime suite | Pass | All 16 `scripts/test_*.sh` gates passed, including R0-R6, failure paths, restart, one-/eight-rank mapping, MVP sources and prescribed fields, MOZART-35, and the three-case bitwise E0 baseline gate. |
| Mixed-unit MPAS run | Pass | An isolated eight-rank lightning-supercell run produced `vmr_O3` in ppmv, `vmr_NO2` in ppbv, and `vmr_NO` in pptv; every conversion and units attribute passed, while all authoritative `q*` fields were exactly equal to the accepted current-stack baseline. |
| Current host-binding compatibility | Pass | The compiled MOZART-35 Fortran contract verifies fixed O2/N2 fractions, field-derived H2O, and transported O2 metadata; the full emissions-contract gate passed. |
| Default MMR compatibility | Pass | The three E0 default runs emitted no additional VMR state and remained bitwise identical for every pinned scientific field. |

### Original branch verification (2026-07-19)

#### Build and focused runtime coverage

| Check | Status | Evidence |
| --- | --- | --- |
| MUSICA-enabled build | Pass | Clean GFortran double-precision build linked with MUSICA-Fortran 0.14.5. |
| Non-MUSICA build | Pass | Clean GFortran double-precision build with `MUSICA=false`; chemistry-unit additions do not affect that configuration. |
| Mixed-unit 8-rank run | Pass | Exercised global `fraction` with `H2O=ppmv`, `O2=percent`, `O=ppbv`, `O1D=pptv`, and `O3=mmr`. Element-wise values, layouts, finite values, and NetCDF units passed. |
| Host-bound `H2O` | Pass | `vmr_H2O` was derived from MPAS `qv` using the MICM H2O molar mass and matched the expected ppmv conversion. |
| Default MMR compatibility | Pass | Default run emitted no `vmr_*` variables, and all `q*` output was exactly equal to the corresponding mixed-unit run. |
| Restart boundary | Pass | Restart output contained authoritative `q*` state and no automatically attached `vmr_*` diagnostics. |
| Invalid configuration | Pass | Unknown MICM species and the invalid unit spelling `ppbt` both failed before integration with actionable messages. |
| Static checks | Pass | `python -m py_compile scripts/check_chem_output.py` and `git diff --check` passed. |

#### Full reference-backed cases

The default and unit-enabled cases were run in isolated directories without
modifying the maintained run cases or reference files. Default comparisons used
zero relative tolerance. Unit-enabled runs first required their `q*` fields to
remain bit-identical to the same MMR reference, then an independent Python
post-processing check evaluated:

```text
expected_vmr = reference_mmr * (0.0289644 / M_species * unit_scale)
```

| Case | Namelist selection | MMR reference result | VMR reference result |
| --- | --- | --- | --- |
| LNOx supercell, 30 minutes, 61 frames | Default `mmr` | `qv`, `qc`, `qr`, `qO3`, `qNO`, and `qNO2` were bit-identical to `supercell_lnox_r11.nc`; no `vmr_*` fields were present. | Not applicable. |
| LNOx supercell, 30 minutes, 61 frames | Global `ppmv` | The same six `q*` fields remained bit-identical to `supercell_lnox_r11.nc`. | `vmr_O3`, `vmr_NO`, and `vmr_NO2` were bit-identical to Python conversions of the corresponding reference MMR arrays; all units were `ppmv`. |
| Chapman-NOx global, 1 hour, 2 frames | Default `mmr` | `qv`, `qNO2`, `qNO`, `qO3`, `qO`, and `qO2` were bit-identical to `chapman_r11.nc`; no `vmr_*` fields were present. | Not applicable. |
| Chapman-NOx global, 1 hour, 2 frames | Global `fraction`; `O2=percent`, `O=ppbv`, `NO=pptv`, `O3=mmr` | The same six `q*` fields remained bit-identical to `chapman_r11.nc`. | `vmr_NO2`, `vmr_O2`, `vmr_O`, and `vmr_NO` were bit-identical to Python conversions of the reference MMR arrays with exact unit metadata; `vmr_O3` was correctly suppressed. |

Together, the focused and full-case tests cover every accepted non-MMR unit,
global selection, per-species precedence, MMR suppression, exact MICM species
matching, host binding, unchanged state output, and history-only diagnostics.

The full-case Python check also exposed an operation-order edge case for
subnormal atomic-O values. The checker now precomputes the conversion factor,
matching the Fortran implementation; the corrected check is bit-exact across
the full Chapman and supercell references.

## Acceptance criteria

- The default configuration preserves current output and numerical behavior.
- `q<species>` remains the sole authoritative transported and restart state.
- Every configured `vmr_<species>` equals the documented conversion from its
  source MMR field within floating-point tolerance.
- Output metadata matches the selected unit.
- Per-species overrides take precedence over the global selection.
- Host-bound MICM species use their MPAS host field.
- Invalid configurations fail before time integration with actionable errors.
- The ABBA seeding path is unchanged.

## Explicitly out of scope

- Changing or removing MICM initial-concentration seeding.
- Reading VMR fields as model input.
- Storing VMR fields in restart files.
- Replacing or renaming internal `q<species>` fields.
- Emitting one species in multiple VMR scales in the same run.
