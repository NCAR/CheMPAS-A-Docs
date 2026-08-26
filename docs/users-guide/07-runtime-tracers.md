# Chapter 7: Runtime Chemistry Tracers

CheMPAS-A treats chemistry tracers as *runtime* state: rather than hard-coding
the species list in `Registry.xml`, the model reads a MICM configuration file
at startup and extends the MPAS `scalars` pool to hold whatever species that
mechanism declares. Switching mechanisms — for example between a stratospheric
Chapman cycle, a tropospheric NOx-O3 mechanism, or the ABBA
coupling-test configuration — requires only changing the MICM config file;
no Fortran source edits, no Registry edits, no rebuild.

This chapter describes how to select a chemistry mechanism, what the runtime
allocation does at startup, and the constraints that come with the dynamic
tracer pool. The features described here are only active in builds compiled
with MUSICA support; see [Section 3.6](03-building.md#36-building-with-chemistry-musica-support)
for build instructions.

## 7.1 Overview

In a stock MPAS-Atmosphere build, every prognostic tracer (`qv`, `qc`, `qr`,
…) is declared in `Registry.xml` and the framework allocates the `scalars`
pool from those static declarations during `atm_setup_block`. CheMPAS-A
keeps those moisture declarations and uses MPAS runtime variables for the
chemistry set. Before pool generation, `atm_setup_block` queries MICM for the
active species and registers a runtime-var callback. The generated
`atm_generate_pools` path then builds the Registry-defined tracers and invokes
that callback for the `scalars` and `scalars_tend` var-arrays. The runtime-var
framework appends the chemistry constituents, updates `num_scalars`, and adds
the per-species `index_qXX` dimensions before field arrays are allocated.
Chemistry tracers thereafter participate in transport, halo exchange, and I/O
exactly like Registry tracers.

## 7.2 Selecting a MICM Configuration

The MICM configuration file is selected via the `config_micm_file` option
in the `&chemistry` namelist record:

```
&chemistry
    config_micm_file = 'lnox_o3.yaml'
/
```

The file name is resolved against the run directory. CheMPAS-A ships
several reference configurations under `micm_configs/`:

| File | Mechanism |
|------|-----------|
| `abba.yaml` | Three-species `AB ⇌ A + B` coupling-test mechanism |
| `chapman.yaml`, `chapman_full.yaml`, `chapman_only.yaml` | Stratospheric Chapman cycle variants |
| `chapman_nox.yaml`, `chapman_nox_no_O.yaml`, `chapman_nox_noO1D.yaml`, `chapman_nox_slow.yaml` | Chapman + NOx variants for stiffness studies |
| `lnox_o3.yaml` | Tropospheric NOx-O3 mechanism used by the LNOx tutorial case |
| `lnox_o3_sink.yaml` | Tropospheric NOx-O3 variant with a relaxation sink |

The `&lnox` record gates lightning NOx, `&photolysis` configures TUV-x
and fallback photolysis, and `&chemistry` holds solver controls such as
sub-stepping and MICM relative tolerance; see Appendix B for the full
namelist reference. Setting `config_micm_file = ''` (the default)
disables chemistry, and the chemistry records can be omitted entirely
from the namelist.

For authoring new MICM mechanisms — species lists, reaction syntax,
rate-parameter formats — refer to the MUSICA documentation at
<https://musica.readthedocs.io/>.

## 7.3 Runtime Tracer Allocation

At model startup, for each MPAS block:

1. `atm_prepare_runtime_chemistry_vars` instantiates a temporary MICM solver
   from `config_micm_file` and caches the q-prefixed MPAS tracer names for
   non-host-bound species.
2. `MPAS_var_add_callback` registers the chemistry runtime-var callback, then
   `atm_generate_pools` generates Registry tracers (`qv`, `qc`, `qr`, …) and
   invokes the callback for `state/scalars` and `tend/scalars_tend`.
3. The callback appends each `qXX` chemistry tracer to `scalars` and each
   `tend_qXX` tendency, with `name_in_code = qXX`, to `scalars_tend`.
4. The framework's block creator (`mpas_block_creator`) allocates field
   arrays from the now-extended `num_scalars`.
5. Chemistry initialization (`chemistry_init`) constructs the persistent
   MICM solver, resolves the per-species `index_qXX` dimensions from the
   pool metadata, and seeds the MPAS scalars from the MICM initial state.
   If any chemistry tracer already contains spatial gradients in the input
   state, the MICM seed is skipped for the whole chemistry set so that
   file-provided tracer fields are preserved.

After this point, chemistry species are first-class scalars: they appear
in output streams under their q-prefixed MPAS tracer names, they are advected
by the dynamics, and they are halo-exchanged on every step.

## 7.4 Constraints and Known Limits

- **Lateral boundary conditions are not supported with runtime tracers.**
  The `lbc_scalars` pool is statically sized from Registry metadata,
  so `config_apply_lbcs = .true.` (regional simulations, see
  [Section 10.2](10-model-options.md#102-regional-simulation)) is
  incompatible with chemistry. Regional chemistry support requires a
  generalization that has not yet been implemented.
- **Scope is intentionally narrow.** CheMPAS-A uses the generic MPAS
  runtime-var framework, but currently registers only the chemistry callback
  for the atmosphere `scalars` and `scalars_tend` var-arrays.
- **Rebuild not required when switching mechanisms**, but the run
  directory must contain the YAML file named by `config_micm_file` and
  any TUV-x supporting files referenced by the chemistry namelist.
