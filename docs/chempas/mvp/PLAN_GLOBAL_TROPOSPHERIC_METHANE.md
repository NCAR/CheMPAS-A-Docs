# Global Tropospheric Methane and MOZART-35 Implementation Plan

**Status:** Implementation complete through the executable qualification layer;
science execution is blocked by unavailable ADS credentials and insufficient
local storage for the required seven-day Tier Z pairs (2026-08-15)

**Target branch:** develop_tropo_methane

**Planning baseline:** 8b003fbd221cfabdff69c553a647a9bf08fbe16b
(Merge branch 'develop_emissions' into develop)

**Current implementation record:** The acquisition/remap/initialization tools,
signed CH4 surface exchange, separate NOx and CH4 inventories, Tier C methane
mechanisms, deterministic MOZART-35 translation, 48-hour MICM/SciPy box
qualification, global gate harness/checker, plotting protocol, and portable
evidence publisher are implemented and tested. The current ADS catalogue audit
passes for the exact v24r2 surface-plus-satellite selection. No CAMS inversion
retrieval, global C/Z promotion result, or Desktop science figure is claimed:
this machine has neither `ADS_API_TOKEN` nor `~/.cdsapirc`, and the acquisition
command stops before submitting a request. See
`docs/chempas/musica/global-methane-runs/d0-data-access-status.md`.
The accepted legacy Tier C state has also been expanded to an audited Tier Z
state with an explicit `legacy_background` CH4 lineage. The current runtime
readiness and frozen per-gate storage requirements are recorded in
`docs/chempas/musica/global-methane-runs/runtime-readiness-status.json`.

**Relationship to accepted work:** This plan builds on the completed global
tropospheric NOx ladder in PLAN_GLOBAL_TROPOSPHERIC_NOX.md. Accepted NOx
inventories, mechanisms, reports, figures, and external evidence remain
immutable. Methane work uses a separate test-case and evidence namespace.

## Goal

Add methane to the global tropospheric workflow in both requested forms:

1. a date-matched, three-dimensional atmospheric CH4 background; and
2. explicit, time-varying surface CH4 sources applied through MIEM.

First qualify those data and coupling paths with the existing reduced
Ox-HOx-NOx-CO-CH4 mechanism. Then translate, couple, and qualify the local
MOZART-35 mechanism as the next tropospheric chemistry tier.

The work is complete when:

- a pinned CAMS inversion CH4 field reproducibly initializes the x1.40962
  atmosphere without changing meteorology, water vapor, mesh, or clock;
- a pinned CAMS posterior CH4 surface-source product is conservatively remapped,
  packaged, applied through MIEM, and closed against runtime diagnostics;
- CAMS-GLOB-ANT CH4 is available as a separate anthropogenic attribution
  experiment and is never added to the posterior total source;
- accepted CAMS NO and NO2 emissions remain present in the main methane
  experiments so that the OH environment is not changed by accidentally
  removing the existing source;
- the reduced chemistry tier passes source, chemistry, restart, budget,
  plotting, and provenance gates;
- MOZART-35 is generated deterministically from its pinned source, passes
  independent chemistry tests, and completes its global promotion ladder;
- public figures follow chempas-science-plot-v1 and include absolute CH4, NO,
  and NO2 column burdens as well as explicit paired differences;
- all new reports and figures are hash-closed and reproducible; and
- the full existing test suite and a fresh release build pass before final
  integration.

## Settled decisions

- **Implement both methane pathways.** Background CH4 and surface CH4 sources
  are separate inputs, separate provenance records, and separate experiment
  axes.
- **Background does not mean a maintained boundary condition.** The CAMS
  three-dimensional field initializes CH4 at the run start. This phase does not
  nudge CH4 or restore it during integration.
- **Use an internally consistent primary pair.** The primary background and
  posterior total surface source come from the same frozen CAMS CH4 inversion
  release and solution family for 2024-07-01.
- **Keep anthropogenic attribution separate.** CAMS-GLOB-ANT v6.2 CH4 is a
  distinct anthropogenic-only experiment. It is not summed with the inversion
  total or with the inversion category named other.
- **Do not double-count fires.** The inversion biomass-burning category already
  incorporates a fire source. Daily GFAS CH4 may be added later only as an
  explicitly named replacement sensitivity, never as an additional source in
  the primary experiment.
- **Retain the accepted NOx source.** NO and NO2 emissions continue in both
  members of every primary CH4 pair. A paired branch changes only the declared
  methane intervention.
- **Use separate exact-grid inventories.** Preserve the accepted NOx NetCDF
  artifact byte-for-byte and stage a second CH4 NetCDF artifact. Prove MIEM's
  multiple-inventory behavior with a synthetic integration test before any
  science run; do not combine and rewrite the accepted NOx fields merely for
  convenience.
- **Qualify coupling before expanding chemistry.** The current
  Ox-HOx-NOx-CO-CH4 mechanism receives CH4 emission reactions and establishes
  the data, source, restart, and budget contracts before MOZART-35 is promoted.
- **Adopt MOZART-35 as the next mechanism.** The name means the 35-tracer subset
  of MOZART-4, not “MOZART 3.5.”
- **Use standard experiment language.** Public text says background,
  surface source applied, surface source withheld, or applied minus withheld.
  It does not use enabled, disabled, unqualified control, or forcing as a
  synonym for emissions.
- **Keep the accepted global date and mesh.** Required gates use the x1.40962
  mesh, 2024-07-01 00:00 UTC start, 450 s dynamics step, and eight MPI ranks
  unless a documented resource gate requires a separately named lower-cost
  development fixture.
- **Do not claim production chemistry.** MOZART-35 is a verified intermediate
  gas-phase subset. This phase does not add deposition, full VOC emissions,
  heterogeneous chemistry, stratospheric chlorine loss, online plume rise, or
  an 85-species MOZART mechanism.

## Source and provenance contracts

### Primary CH4 background and posterior source

Use the
[CAMS global inversion-optimised greenhouse-gas product](https://ads.atmosphere.copernicus.eu/datasets/cams-global-greenhouse-gas-inversion?tab=overview).
It supplies model-level CH4 dry mole fraction, column-mean dry mole fraction,
and monthly surface upward CH4 fluxes. The acquisition record must freeze:

- the exact release and solution identifier;
- whether the solution assimilates surface observations only or surface plus
  satellite observations;
- the ADS request JSON and retrieval timestamp;
- all requested variables, levels, valid times, coordinates, and units;
- provider metadata and licence/citation text;
- file sizes and SHA-256 hashes; and
- the relationship between the concentration and flux products.

The implementation target is the v24r2 surface-plus-satellite solution for
2024-07-01 if that exact solution identifier is exposed by the current ADS
request API. Stage D0 must confirm the identifier rather than infer it from a
filename. If it is unavailable, stop at D0 and record the available solution
identifiers; do not silently substitute another release.

Request at minimum:

- CH4 dry mole fraction on all available model levels at the exact initial
  timestamp and any time brackets required by the provider representation;
- CH4 total-column dry mole fraction for an independent remap check;
- total surface upward CH4 mass flux; and
- wetlands, rice, biomass-burning, and other surface-flux components.

The
[CAMS CH4 inversion production documentation](https://confluence.ecmwf.int/spaces/CKB/pages/488281456/Description%2Bof%2Bthe%2BCH4%2Binversion%2Bproduction%2Bchain)
states that other includes remaining sources and soil sinks. Therefore other
is a provider-defined posterior category, not an anthropogenic label. Preserve
it as other in metadata, diagnostics, and figures.

### Anthropogenic attribution source

Use CH4 from the same frozen CAMS-GLOB-ANT v6.2 archive already accepted for
global NOx in the
[CAMS global emission inventories](https://ads.atmosphere.copernicus.eu/datasets/cams-global-emission-inventories?tab=overview),
retaining the provider's sector fields and monthly timestamps. The acquisition
workflow must retrieve the native methane variable rather than derive CH4 from
another species.

This product is used only in a separately named anthropogenic CH4 pair. It is
not a component that can be added to the posterior total-source experiment.

### Independent observational benchmark

Use the
[NOAA Global Monitoring Laboratory CH4 monthly mean](https://gml.noaa.gov/ccgg/trends_ch4/)
as an external scalar plausibility benchmark for marine-boundary-layer dry-air
mole fraction. It is not an initializer, a tuning target, or a replacement for
three-dimensional CAMS structure.

### Data semantics

- Atmospheric CH4 input is a dry-air mole fraction in mol mol-1, normally
  displayed as ppb.
- Surface source input is kg CH4 m-2 s-1.
- CH4 column burden is moles of CH4 m-2 over a stated vertical domain.
- Global atmospheric burden is reported in mol CH4, kg CH4, and Tg CH4 with one
  shared conversion implementation.
- Carbon-family budgets are reported in mol C.
- Inventory timestamps and model timestamps are UTC.
- Monthly fields use the provider's stated temporal semantics. Any interpolation
  is recorded with its two source brackets and exact weights.
- Missing values, NaN, Inf, negative concentration, or undocumented units are
  hard failures.
- No negative surface flux may be clipped. If the selected posterior field
  contains negative values, Stage E0 must demonstrate an explicit signed
  source/sink coupling and budget before promotion; an EMISSION reaction alone
  is not assumed to represent uptake.

## Chemistry tiers

### Tier C: Existing reduced methane chemistry

Create:

- micm_configs/global_cams_tropo_ch4nox_ch4.yaml
- micm_configs/global_cams_tropo_ch4nox_ch4_strict.yaml

Derive them mechanically from the accepted global_cams_tropo_ch4nox files.
Preserve every existing species, reaction, rate, and calibrated tolerance, then
add exactly these MIEM entry points:

    EMIS.NO  -> NO
    EMIS.NO2 -> NO2
    EMIS.CH4 -> CH4

Each coefficient is one molecule of mechanism species per molecule supplied by
MIEM. CH4 requires no chemical speciation factor. The existing NO and NO2
entry points remain unchanged.

Tier C answers whether the new background, methane source, MIEM coupling,
budgets, restarts, and diagnostics work in the already accepted reduced
chemistry. It is not an independent full-mechanism evaluation.

### Tier Z: MOZART-35

The upstream local source is:

    /home/fillmore/EarthSystem/MPAS-MATCH/docs/match/mozart35.yaml

Freeze the source-introducing commit
224ff2032ada178db6cfef2c44f8a38e57cc02dc and source SHA-256
1b8c3ee939b113c5d05d30d131d358716edd066449929cf8c960a4f9ec93c559.
The source describes 35 integrated tracers, 71 gas reactions, 18 photolysis
reactions, and explicit terminal C/N/S products, based on
[Emmons et al. (2010)](https://gmd.copernicus.org/articles/3/43/2010/).

Vendor those exact source bytes, with their provenance and licence notice, as
micm_configs/sources/mozart35.yaml. The repository-local snapshot is the
translator input so a clean CheMPAS-A checkout does not depend on the adjacent
MPAS-MATCH working tree. Its hash must equal the upstream hash above.

Create a deterministic translator and generated artifacts:

- scripts/generate_micm_mozart35.py
- micm_configs/global_cams_mozart35.yaml
- micm_configs/global_cams_mozart35_strict.yaml
- micm_configs/tuvx_mozart35.json
- a machine-readable source-to-MICM mapping and generation manifest.

The translator must:

- consume the pinned repository-local MOZART-35 YAML rather than transcribing
  reactions by hand;
- verify source hash, species count, reaction counts, formulas, molar masses,
  and declared rate units before generation;
- convert cgs molecule-based rate constants to MICM SI units explicitly;
- map Arrhenius, Troe, equilibrium-decomposition, and special rates without
  flattening pressure or water-vapor dependence;
- map all 18 photolysis channels one-to-one to TUV-x names;
- preserve reaction names and source-table identifiers;
- retain terminal-product stoichiometry in an audit sidecar;
- add only EMIS.NO, EMIS.NO2, and EMIS.CH4 for this phase;
- emit stable, reproducible ordering and byte-identical output; and
- fail on any unsupported rate form or unmapped product.

Do not reuse the eight-channel Tier C TUV-x configuration. The 18-channel
configuration must be strict JSON and must be checked against the generated
MICM reaction inventory.

The existing MPAS-MATCH verification is valuable upstream evidence but is not a
CheMPAS-A pass. Its 24-hour transient reported a 5.634-year instantaneous CH4
lifetime and weak OH spatial-pattern agreement. Those limitations remain
visible until the real background, emissions, online TUV-x, and CheMPAS-A
transport experiments test them. No acceptance threshold may be relaxed merely
to reproduce that transient.

## Scientific and software contracts

### Three-dimensional initialization

Start from the pinned date-matched GFS x1.40962 state and always write a new
NetCDF file.

Reconstruct CAMS source-layer pressures from the published vertical-coordinate
metadata. Remap CH4 by conserving the CH4 numerator and dry-air denominator:

1. derive source-cell dry-air moles for every source layer;
2. multiply by source CH4 dry mole fraction to obtain CH4 moles;
3. conservatively remap dry-air and CH4 moles horizontally;
4. remap both through exact source/destination pressure-layer overlap; and
5. divide the remapped quantities to recover destination dry mole fraction.

This is preferred over direct interpolation because it supplies a closed global
burden audit. Terrain and below-ground source layers, source-top coverage, and
destination layers above the source top must each have an explicit,
machine-tested policy. No extrapolation may be hidden in a library default.

Convert the destination dry mole fraction to the documented MPAS chemistry
tracer convention, dry-air mass mixing ratio, using the shared model constants:

    qCH4 = xCH4 * M_CH4 / M_dry_air
    M_CH4 = 0.016043 kg mol-1
    M_dry_air = 0.0289644 kg mol-1

The unit test must recover the original dry-air mole fraction from the written
state and must use the same constants as the runtime coupler.

The initializer must:

- preserve mesh identity, dimensions, valid time, and non-chemistry variables;
- preserve qv and every meteorological field bit-for-bit;
- replace the legacy analytic CH4 profile only in the new methane state;
- write finite, nonnegative qCH4 with units, long name, and source metadata;
- report native and destination surface, column, and global CH4 statistics;
- compare the remapped column mean against the provider XCH4 field;
- compare a declared marine-boundary-layer diagnostic against NOAA without
  tuning;
- record source and output hashes, remap weights, formulas, constants, and
  software commit; and
- reproduce byte-identical output from identical inputs.

For Tier Z, common tracers inherit the accepted expanded-chemistry state where
the species definitions agree. Additional long-lived species use versioned,
reviewed profiles derived from the MOZART-35 source verification; fast
intermediates may start at zero or a documented floor only before a mandatory
chemistry spin-up. Every species receives a provenance class in the initial
condition audit. CH4 always comes from the CAMS field.

### Surface-source remap and MIEM packaging

Generalize the current NOx-only acquisition/remap helpers into shared inventory
infrastructure while retaining wrapper compatibility and byte-identical NOx
behavior.

For every CH4 time and category:

- validate coordinate bounds, calendars, units, missing values, and provider
  totals;
- use first-order conservative ESMF remapping with canonical cell areas;
- require all source and destination cells to be mapped;
- retain the accepted 2.0e-7 relative tolerance for remap weights and
  field-integrated mass;
- package exact-grid fluxes without runtime horizontal regridding;
- map inventory CH4 directly to mechanism CH4 with factor 1.0;
- inject at the surface for this phase;
- retain provider categories and anthropogenic sectors in diagnostics; and
- record native, remapped, and packaged source totals at every time.

Create separate MIEM configurations for posterior-total and anthropogenic-only
experiments. Each configuration references the unchanged NOx inventory and one
CH4 inventory. A synthetic two-inventory test must prove file discovery,
independent time interpolation, source summation, diagnostics, restart behavior,
and a clear failure for either missing file.

Do not rewrite the NOx artifact into a combined file. If the current runtime
cannot open two declared inventories, implement and test that missing MIEM
capability before continuing.

### Runtime source accounting

For each output interval, independently integrate:

- prescribed CH4 surface flux over cell area and time;
- MIEM-applied CH4 mass and moles;
- NO and NO2 source moles from the unchanged accepted path; and
- category/sector subtotals.

Inventory integration and MIEM diagnostics must close with combined
relative/absolute tolerances frozen before the first science result. Adjacent
intervals and cumulative totals are both checked. A clean model exit without
this closure is not a pass.

### Carbon, nitrogen, and sulfur accounting

CH4 burden change is not equal to emitted CH4 once chemistry is active. The
required paired global carbon identity is:

    delta active carbon
      + delta terminal carbon ledger
      = integrated applied CH4 carbon

The active family counts every carbon atom in every integrated mechanism
species. The terminal ledger counts carbon transferred to omitted terminal
products such as CO2. It must be driven by the same reaction rates, written to
history and restart, and remain continuous across split runs.

For Tier Z, apply the same active-plus-terminal construction to nitrogen and
sulfur. With NO and NO2 as the only added nitrogen source and no deposition:

    delta active nitrogen
      + delta terminal nitrogen ledger
      = integrated applied NO plus NO2 nitrogen

With no sulfur source or sink in this phase, active plus terminal sulfur is
constant apart from bounded numerical residual.

Tier C requires at least a carbon terminal diagnostic for its omitted CO2
product. If the MICM interface cannot expose the required reaction-rate
increments, add a generic restart-safe elemental-ledger interface before
claiming carbon closure. Do not substitute CH4-only burden closure.

Also report, without treating them as conservation identities:

- CH4 chemical loss by OH and O(1D);
- tropospheric and full-domain burden divided by the corresponding integrated
  chemical loss, labeled as model-domain chemical lifetime;
- OH, HO2, O3, CO, CH2O, and organic-reservoir responses;
- all configured photolysis rates; and
- below/above 150 hPa contributions.

### Experiment isolation

Use matched branches that differ in exactly one declared methane intervention.

**Background sensitivity**

- CAMS three-dimensional background versus the legacy analytic background;
- identical NOx and CH4 source treatment in both members;
- identical meteorology, chemistry, clock, source lineage, and matched spin-up
  schedule, while retaining the deliberately different initial CH4 fields; and
- interpreted as initialization sensitivity, not an emissions response.

**Posterior total-source response**

- one posterior-source common spin-up with the CAMS background, accepted NOx
  emissions, and posterior CH4 source applied;
- analysis branch A continues the posterior CH4 source;
- analysis branch B withholds only that CH4 source;
- NO and NO2 emissions continue in both branches; and
- the reported response is continued minus withheld over the stated interval.

**Anthropogenic attribution**

- one separate anthropogenic-source common spin-up with the CAMS background,
  accepted NOx emissions, and CAMS-GLOB-ANT v6.2 CH4 applied;
- branch A applies CAMS-GLOB-ANT v6.2 CH4;
- branch B withholds that anthropogenic CH4 source;
- no posterior-total CH4 source is present in the spin-up or either analysis
  member; and
- results are anthropogenic source attribution, not a component of the
  posterior-total response.

Do not compare a changed background and a changed source in the same pair.
Do not label any withheld branch as pristine: it inherits atmospheric CH4 and,
after its source-specific common spin-up, previously applied emissions.

### Restart and determinism

Every promoted split experiment must:

- use an immutable, hash-verified common restart;
- reproduce continuous output at common timestamps within predeclared
  species-wise tolerances;
- preserve cumulative source and elemental ledgers across restart;
- recompute photolysis from absolute UTC rather than elapsed segment time;
- prove source-response branches have identical inputs except for the declared
  CH4 source selection, and prove background-sensitivity branches differ only
  in their declared CH4 initialization lineage; and
- record executable, dependency, configuration, state, inventory, restart,
  history, and report hashes.

## Implementation stages

### Stage 0: Freeze baseline and test inventory

- [x] Record the branch point, submodule/dependency commits, compiler and
  library versions, accepted NOx artifact hashes, and canonical external roots.
- [x] Inventory all canonical unit/static tests and accepted science
  reproducers; record counts without baking a soon-stale count into scripts.
- [x] Run the complete current test suite and a fresh release build before
  methane code changes.
- [x] Confirm the existing global NOx evidence is clean and is not rewritten by
  the new harness.
- [x] Create a stage-0 report with commands, durations, outcomes, and hashes.

**Promotion:** clean baseline tests/build, immutable NOx evidence, and a
complete provenance snapshot.

### Stage 1: Acquire and qualify source data (D0)

- [x] Implement a parameterized ADS request layer with recorded request JSON,
  retries, checksums, and no implicit latest selection.
- [ ] Retrieve the exact CAMS inversion concentration, XCH4, total flux, and
  four component fields for 2024-07-01.
- [x] Retrieve CAMS-GLOB-ANT v6.2 CH4 sectors from the same accepted archive
  lineage as NOx.
- [ ] Validate coordinates, levels, timestamps, calendars, units, missing
  values, category sums, signs, and global totals.
- [x] Pin NOAA benchmark data and its retrieval metadata.
- [x] Write compact source-selection and acquisition reports; keep large
  NetCDF files outside Git.

**Promotion:** exact product identities are frozen, provider fields are
internally consistent, and every input has a size and SHA-256 record.

### Stage 2: Generalize conservative inventory preparation (E0)

- [x] Separate generic grid, unit, time, ESMF, packaging, and hash utilities
  from NOx-specific speciation logic.
- [x] Retain compatibility imports or wrappers so all existing NOx tests and
  generated hashes remain unchanged.
- [x] Add analytic constant, patterned, monthly-interpolation, and conservation
  fixtures for one-species CH4.
- [x] Remap and package the anthropogenic sectors as a separate exact-grid MIEM
  inventory.
- [ ] Remap and package the posterior total/components as a signed exact-grid
  MIEM inventory.
- [x] Add a two-inventory runtime fixture containing unchanged NOx plus CH4.
- [x] Verify missing-file, unit, time, negative-flux, and mesh-mismatch
  failures.

**Promotion:** all remap/source budgets pass, two inventories work
independently, and accepted NOx behavior is byte-for-byte unchanged.

### Stage 3: Build the three-dimensional initial state (B0)

- [x] Implement pressure reconstruction and conservative 3-D CH4 remapping.
- [x] Add unit tests for horizontal weights, vertical overlap, terrain,
  top/bottom handling, and dry-air conversion.
- [ ] Generate the Tier C CAMS-background state from the pinned GFS state.
- [ ] Audit bitwise preservation of qv and every non-target field.
- [ ] Verify native/remapped global burden and provider-XCH4 consistency.
- [ ] Compare the declared marine-boundary-layer diagnostic with NOAA.
- [x] Retain the separately named, accepted legacy-background Tier C state for
  sensitivity only.
- [ ] Produce the deterministic CAMS-state audit JSON and concise report.

**Promotion:** B0 is finite, nonnegative, burden-closed, bitwise safe outside
declared chemistry fields, and reproducible.

### Stage 4: Tier C mechanism, diagnostics, and harness (C0)

- [x] Generate normal and strict Tier C mechanisms with EMIS.CH4.
- [x] Test species/reaction inventories, elemental formulas, units, rate
  matrices, and exact preservation of accepted reactions.
- [x] Add restart-safe CH4 source, chemical-loss, burden, and carbon-ledger
  diagnostics.
- [x] Create test_cases/global_methane_miem with schema-validated scenarios,
  overlays, stream files, and a separate external-data namespace.
- [x] Extend the runner to select background, CH4 source family, applied or
  withheld analysis state, and immutable restart.
- [x] Reject contradictory source selections and the simultaneous posterior
  plus anthropogenic CH4 combination.
- [x] Add paired-input diff checks that enumerate the one allowed difference.

**Promotion:** box/column tests close source and carbon accounting, strict and
production solvers agree within calibrated bounds, and the harness fails
unsafe configurations before launch.

### Stage 5: Tier C global ladder

- [ ] C1: one-hour global shakedown with the CAMS background, accepted NOx,
  and posterior CH4 source.
- [ ] CPS: 48-hour common fast-chemistry spin-up with accepted NOx and the
  posterior CH4 source applied; register one immutable restart.
- [ ] C2: six-hour continuous/split restart comparison from CPS.
- [ ] C3: 24-hour posterior-source continued/withheld pair from CPS.
- [ ] CAS: separate 48-hour common spin-up with accepted NOx and
  anthropogenic CH4 applied, with no posterior source; register one immutable
  restart.
- [ ] CA3: 24-hour anthropogenic-source continued/withheld pair from CAS.
- [ ] CB3: matched 48-hour spin-ups plus 24-hour analyses for the CAMS and
  legacy backgrounds, with identical NOx and CH4 source treatment throughout.
- [ ] Audit all intervals for source closure, carbon closure, finite state,
  material negativity, solver events, photolysis, host binding, and resources.
- [ ] Freeze Tier C thresholds and evidence before Tier Z implementation.

**Promotion:** every Tier C report passes and clearly distinguishes background
sensitivity, posterior source response, and anthropogenic attribution.

### Stage 6: Translate and qualify MOZART-35 (Z0)

- [x] Implement deterministic source verification and translation.
- [x] Reproduce the 35 species, 71 gas reactions, 18 photolysis reactions, and
  terminal-product element coefficients.
- [x] Independently test representative Arrhenius, Troe,
  equilibrium-decomposition, water-dependent, DMS, and CO+OH rates over a
  pressure/temperature/humidity matrix.
- [x] Compare an independent Python/SciPy box integrator with MICM for 48 hours.
- [x] Check analytic/numerical Jacobian agreement and every-reaction C/N/S
  closure including terminal products.
- [x] Calibrate production tolerances against a stricter solver without
  changing chemistry coefficients.
- [x] Generate and validate the 18-channel TUV-x configuration.
- [x] Record differences from the upstream MPAS-MATCH implementation.

**Promotion:** generated files are byte-reproducible, all translations are
mapped, independent box/rate/conservation tests pass, and no unsupported
reaction is approximated silently.

### Stage 7: Couple MOZART-35 to MPAS (Z1)

- [x] Add all required q-species registry fields, metadata, streams, history,
  restart, and scalar lookup in stable mechanism order.
- [x] Bind M, H2O, O2, and N2 using the documented moist/dry-air semantics.
- [x] Implement or connect generic terminal C/N/S ledgers.
- [x] Require explicit CAMS-versus-legacy CH4 lineage and create the audited
  Tier Z legacy state with one provenance class for every tracer.
- [ ] Create the Tier Z CAMS state with one provenance class for every tracer.
- [x] Prove chemistry-off and existing Tier C runs do not change in schema or
  payload because the new Registry fields exist.
- [x] Run synthetic source and one-column tests for EMIS.NO, EMIS.NO2, and
  EMIS.CH4.
- [x] Confirm the supported one-block-per-MPI-task decomposition and fail early
  for unsupported layouts.

**Promotion:** registry/coupler regressions pass, every tracer and photolysis
field is mapped, elemental ledgers close, and legacy modes remain unchanged.

### Stage 8: MOZART-35 global ladder

- [ ] Z1: one-hour global shakedown with real background, NOx, and posterior
  CH4 source.
- [ ] ZPS: 48-hour common radical spin-up with accepted NOx and the posterior
  CH4 source applied; register one immutable restart.
- [ ] Z2: 24-hour continuous/split restart and ledger comparison from ZPS.
- [ ] Z3: seven-day posterior-source continued/withheld experiment from ZPS.
- [ ] ZAS: separate 48-hour common radical spin-up with accepted NOx and
  anthropogenic CH4 applied, with no posterior source; register an immutable
  restart.
- [ ] ZA3: seven-day anthropogenic-source continued/withheld experiment from
  ZAS.
- [ ] ZB3: matched 48-hour spin-ups plus seven-day analyses for the CAMS and
  legacy backgrounds, with identical NOx and CH4 source treatment throughout.
- [ ] Diagnose CH4 loss and lifetime from integrated reaction loss, not from a
  small noisy endpoint difference alone.
- [ ] Compare OH pattern and model-domain CH4 lifetime with the upstream
  MOZART-35 result and published context without tuning to either.
- [ ] Forecast cost and storage from Z1/ZPS before Z3 launch and enforce the
  existing resource/output-volume contracts.

A 30-day Z4 extension is configured but not required for implementation
promotion. It is required before making a monthly source-response or
climatological lifetime claim. The seven-day ladder supports coupling,
stability, restart, and short-timescale process conclusions only.

**Promotion:** Z1, ZPS, Z2, Z3, ZAS, ZA3, and ZB3 pass all source, chemistry,
restart, elemental, physical-range, and resource checks, with limitations
stated.

### Stage 9: Plots, evidence, documentation, and full regression

- [x] Implement and test the methane figure bundle described below.
- [ ] Produce 300-dpi PNG and vector PDF pairs only from passed, hash-verified
  histories.
- [ ] Open every PNG at full resolution and record visual inspection.
- [ ] Publish schemas, compact reports, figure manifest, and reproduction guide
  under the methane namespace.
- [x] Run every canonical Python/C++/shell test, mechanism reproducer, strict
  JSON check, and git diff --check.
- [x] Perform a clean release build against the pinned MUSICA dependency.
- [x] Run accepted chemistry-off, MIEM, Stage 9, and global-tropospheric NOx
  regression gates unchanged.
- [x] Confirm no untracked or user-owned file was included in a checkpoint.
- [x] Record final command results, test counts, build hashes, executable hash,
  dependency commits, and external artifact hashes.

**Promotion:** all tests and the clean build pass, all required science gates
are promotable, and the documentation reproduces the complete workflow from a
clean checkout plus declared external inputs.

## Promotion ladder summary

| Gate | Duration | Tier | Purpose | Required result |
|---|---:|---|---|---|
| D0 | static | Data | Product identity and source audit | Pinned requests, units, signs, hashes |
| E0 | synthetic/static | MIEM | CH4 remap and two inventories | Mass closure and unchanged NOx |
| B0 | static | Initial state | 3-D background remap | Burden closure and bitwise host fields |
| C0 | box/column | Tier C | Mechanism and budget wiring | Rates, source, carbon ledger pass |
| C1 | 1 h | Tier C | Global shakedown | Stable source/chemistry coupling |
| CPS | 48 h | Tier C | Posterior-source spin-up | Qualified immutable restart |
| C2 | 6 h | Tier C | Restart | Continuous/split equivalence |
| C3 | 24 h | Tier C | Posterior-source response | Full paired audit |
| CAS | 48 h | Tier C | Anthropogenic-source spin-up | Qualified immutable restart |
| CA3 | 24 h | Tier C | Anthropogenic attribution | Separate paired audit |
| CB3 | 48 h + 24 h | Tier C | Background sensitivity | One-axis paired audit |
| Z0 | 48 h box | Tier Z | Translation and chemistry | Independent parity/C-N-S closure |
| Z1 | 1 h | Tier Z | Global shakedown | 35-species/18-rate stability |
| ZPS | 48 h | Tier Z | Posterior-source spin-up | Qualified immutable restart |
| Z2 | 24 h | Tier Z | Restart and ledgers | Continuous/split equivalence |
| Z3 | 7 d | Tier Z | Posterior-source response | Full paired science audit |
| ZAS | 48 h | Tier Z | Anthropogenic-source spin-up | Qualified immutable restart |
| ZA3 | 7 d | Tier Z | Anthropogenic attribution | Separate paired science audit |
| ZB3 | 48 h + 7 d | Tier Z | Background sensitivity | One-axis paired science audit |
| Z4 | 30 d optional | Tier Z | Monthly extension | Required only for monthly claims |

## Scientific plotting contract

Every figure follows docs/chempas/guides/PLOTTING_PROTOCOL.md and
chempas-science-plot-v1.

### Required semantics

- Main titles are concise Title Case with proper CH4, NO, NO2, OH, and
  MOZART-35 notation.
- Subtitles state gate/experiment, inclusive UTC start and end, spatial and
  vertical domain, comparison, and whether the data are instantaneous or a
  time-weighted interval mean.
- A final history record is labeled instantaneous even after a 24-hour or
  seven-day run.
- A daily mean is used only after explicit time integration over the stated
  UTC day. The manifest records the weighting/integration method and source
  records.
- Applied-minus-withheld differences use a zero-centered diverging scale with
  symmetric limits.
- Absolute positive quantities use a sequential scale.
- Column labels state diagnostic troposphere (p >= 150 hPa) or full model
  column.
- Individual species burdens use moles of that species. Family plots state
  their element basis and exact membership.
- Public figures never use enabled, disabled, forcing, or an unqualified
  control label.

### Required primary bundle and order

1. **Methane Surface Sources**
   - posterior total and provider-category flux;
   - anthropogenic sector flux in a separate figure;
   - source brackets, valid interval, and kg CH4 m-2 s-1.

2. **Initial Methane Background**
   - surface dry mole fraction;
   - total-column dry mole fraction;
   - latitude-pressure cross section; and
   - CAMS-minus-legacy background difference.

3. **Atmospheric Methane State and Response**
   - absolute CH4 diagnostic-tropospheric column burden for the
     source-applied/continued branch;
   - explicit applied/continued-minus-withheld CH4 column difference;
   - XCH4 and global burden time series; and
   - instantaneous maps and computed daily means as separately labeled
     products.

4. **Source, Burden, and Chemical Loss**
   - accumulated surface source, atmospheric CH4 burden change, OH/O(1D)
     chemical loss, active carbon, and terminal carbon ledger;
   - interval and cumulative closure residuals; and
   - model-domain chemical lifetime with its domain and loss reactions.

5. **Oxidation and Ozone Response**
   - OH, HO2, CO, CH2O, and O3 absolute state and paired response;
   - day/night context and relevant photolysis rates; and
   - MOZART-35 reservoirs such as PAN where supported.

6. **Nitrogen State and Partitioning**
   - absolute NO and NO2 diagnostic-tropospheric column burdens;
   - continued-minus-withheld NO and NO2 column differences;
   - hourly NO/NO2 burden histories; and
   - HNO3/PAN/NOy partitioning appropriate to the mechanism.

7. **Vertical Structure**
   - latitude-pressure CH4, OH, O3, NO, and NO2 state and paired response;
   - pressure decreasing upward; and
   - the 150 hPa diagnostic boundary drawn and labeled.

Restart, concentration ranges, elemental residuals, performance, memory, and
output volume remain required supplemental figures. They do not replace the
primary source-state-response narrative.

The figure manifest records the protocol and style hashes, plotter and schema
hashes, experiment semantics, averaging method, selected history hashes, and
rendered PNG/PDF hashes.

## Planned tracked artifacts

    PLAN_GLOBAL_TROPOSPHERIC_METHANE.md
    micm_configs/
      sources/mozart35.yaml
      global_cams_tropo_ch4nox_emissions.yaml
      global_cams_tropo_ch4nox_emissions_strict.yaml
      global_cams_mozart35.yaml
      global_cams_mozart35_strict.yaml
      tuvx_mozart35.json
      mozart35-generation-manifest.json
    miem_configs/
      global_cams_nox_ch4_posterior.yaml
      global_cams_nox_ch4_anthropogenic.yaml
    test_cases/global_methane_miem/
      README.md
      scenarios.yaml
      external-inputs.schema.json
      report and figure schemas
      stream_list.atmosphere.*
    scripts/
      acquire_cams_methane_inversion.py
      acquire_global_methane_inventory.py
      remap_global_methane_inventory.py
      remap_global_methane_posterior.py
      prepare_global_methane_initial_condition.py
      prepare_mozart35_initial_condition.py
      prepare_global_methane_runtime_manifest.py
      prepare_zero_miem_inventory.py
      generate_micm_mozart35.py
      qualify_mozart35_box.py
      global_methane_harness.py
      run_global_methane_integration.py
      check_global_methane_runs.py
      plot_global_methane.py
      publish_global_methane_evidence.py
      shared inventory/remap utilities
    tests/
      methane data/acquisition/remap tests
      methane initial-condition tests
      MIEM two-inventory and source tests
      Tier C mechanism/budget/harness tests
      MOZART-35 translation/rate/parity tests
      Registry/coupler/restart tests
      plotting-protocol and evidence-schema tests
    docs/chempas/musica/
      GLOBAL_TROPOSPHERIC_METHANE.md
      global-methane-runs/
        source-selection.json
        acquisition and remap audits
        d0-data-access-status.{json,md}
        implementation-verification.md
        runtime-readiness-status.json
        tier-z-legacy-initial-condition-audit.json
        initial-condition-audits/
        tier-c-*.json
        mozart35-*.json
        figures/
        figure-manifest.json

Large provider files, remap weights, prepared inventories, initial states,
executables, histories, restarts, and logs remain outside Git under a declared
CHEMPAS data root and are referenced by size and SHA-256.

## Checkpoint discipline

- Implement one stage or separately named gate at a time.
- Run scoped tests plus unchanged NOx/MIEM regressions before every checkpoint.
- Do not amend accepted NOx science reports or regenerate their figures.
- Do not promote a run from exit status alone; its schema-validated checker
  must pass every predeclared assertion.
- Freeze thresholds before inspecting the corresponding science comparison.
- Preserve all unrelated tracked and untracked user files.
- Record code commit, dependencies, executable, configurations, source data,
  initial state, inventory, restart, histories, reports, and figures by hash.
- Commit or push only when explicitly requested at implementation time.

## Known limitations and hard stop conditions

- ADS access and exact release naming must be verified at D0. Missing
  credentials or an unavailable v24r2 surface-plus-satellite product blocks
  data promotion rather than authorizing substitution.
- A negative posterior flux blocks science runs until signed uptake is
  represented and tested; clipping is prohibited.
- A failed multiple-inventory fixture blocks science runs; rewriting accepted
  NOx fields is not the fallback.
- An unsupported MOZART-35 rate or terminal product blocks deterministic
  translation; coefficient approximation is not allowed.
- The current all-column chemistry coupling extends above the diagnostic
  troposphere. Results above 150 hPa are reported separately and are not
  interpreted as complete stratospheric methane chemistry.
- No deposition means HNO3, PAN, sulfur, and aerosol interpretation is limited.
- Only CH4, NO, and NO2 emissions are introduced in this phase. Missing VOC,
  CO, sulfur, and other source families limit OH and ozone realism.
- CH4 is long-lived. A one-day or seven-day perturbation does not validate a
  climatological methane trend or atmospheric lifetime.
- MOZART-35 remains a 35-of-85-species subset. Passing this ladder does not
  establish equivalence to full MOZART-4.

## Final completion checklist

- [x] Baseline full tests and clean build are recorded before changes.
- [ ] CAMS three-dimensional CH4 and posterior source share one pinned release
  and complete provenance.
- [x] CAMS-GLOB-ANT CH4 is a separate, non-additive attribution input.
- [ ] CH4 initial-state remap is burden-conserving and preserves host fields
  bit-for-bit.
- [ ] CH4 source remap and runtime application close at every interval.
- [x] Accepted NOx inventory and evidence remain unchanged.
- [x] MIEM opens the separate NOx and CH4 inventories correctly.
- [ ] Tier C passes C0, C1, CPS, C2, C3, CAS, CA3, and CB3.
- [x] MOZART-35 generation is deterministic and independently qualified.
- [ ] Tier Z passes Z0, Z1, ZPS, Z2, Z3, ZAS, ZA3, and ZB3.
- [ ] Source, active-family, terminal-ledger, restart, photolysis,
  non-negativity, physical-range, and resource contracts pass.
- [ ] Figures include absolute CH4, NO, and NO2 columns and explicit paired
  responses with correct time semantics.
- [ ] Every claimed daily mean is explicitly time-integrated and labeled.
- [ ] All reports, histories, and figures are hash-closed.
- [x] Full canonical tests, accepted regressions, mechanism reproducers,
  strict-JSON checks, git diff --check, and a fresh release build pass.
- [x] Final documentation distinguishes coupling correctness, short-timescale
  process response, mechanism behavior, and capabilities still required for
  climatological or production conclusions.
