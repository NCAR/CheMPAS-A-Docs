# Chapter 3: Chapman + NOx Photostationary State

```{admonition} Work in progress
:class: warning

This chapter is being actively written. Commands and expected output
are provisional; figure slots are left without rendered PNGs until the
corresponding model runs and plots are archived.
```

The Chapman + NOx photostationary-state (PSS) tutorial walks through a
small-domain integration of the Chapman ozone cycle plus NOx, with
TUV-x photolysis driven by an extended atmosphere column that reaches
above the model lid. The analytical Leighton expression for [NO]/[NO₂]
under steady-state photolysis is a clean numerical sanity check on the
coupled MICM + TUV-x configuration.

## 3.1 What you'll learn

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

By the end of this chapter you will:

- Run the Chapman + NOx idealized stratospheric-chemistry case in
  CheMPAS-A on the supercell mesh.
- Generate the TUV-x upper-atmosphere extension CSV and understand
  why TUV-x needs photons from above the model lid.
- Verify the chemistry against the analytical Leighton photostationary
  state, then use the maintained output checker and regression contracts.

## 3.2 The Chapman + NOx case

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

The Chapman cycle is the canonical four-reaction pure-oxygen
photochemistry that maintains a stratospheric ozone column:

$$
\begin{aligned}
\mathrm{O_2} + h\nu &\rightarrow 2\,\mathrm{O} \\
\mathrm{O} + \mathrm{O_2} + \mathrm{M} &\rightarrow \mathrm{O_3} + \mathrm{M} \\
\mathrm{O_3} + h\nu &\rightarrow \mathrm{O} + \mathrm{O_2} \\
\mathrm{O} + \mathrm{O_3} &\rightarrow 2\,\mathrm{O_2}
\end{aligned}
$$

Adding NOx introduces the catalytic
NO–NO₂–O₃ cycle (NO + O₃ → NO₂ + O₂; NO₂ + hν → NO + O), which
modulates ozone titration by tying its evolution to NOx photolysis.
On any timescale longer than a few seconds, [NO] / [NO₂] in sunlight
relaxes to the **Leighton photostationary state**, the analytical
target of section 3.7.

The MICM solver evolves all six prognostic species (O₂, O, O¹D, O₃,
NO, NO₂) every timestep — including O₃, which is produced by
O + O₂ + M → O₃ and destroyed by both photolysis and titration.
The Chapman O₃ column itself is *not* prescribed. What `init_chapman.py`
does is supply realistic *initial conditions*: starting the run from
zero would force the chemistry to build the column from scratch, which
takes hours in the upper stratosphere where jO₂ is non-negligible and
months-to-years in the lower stratosphere where the Schumann–Runge
bands are extinguished. The AFGL mid-latitude-summer climatology gets
the run close enough to a reasonable starting state that the diurnal
photochemistry the run actually demonstrates is meaningful.

The Chapman cycle is global-stratospheric physics, but
`scripts/init_chapman.py` seeds a 1-D AFGL mid-latitude-summer ozone
profile uniformly across the supercell mesh, and the chemistry has no
feedback on dynamics. This chapter therefore uses the small
(~85 km × 85 km × 50 km top) supercell grid as a column-like sandbox
— what matters is the vertical structure of the photolysis driver and
the chemistry's ability to settle into the PSS, both of which TUV-x
sees through the column extension introduced in section 3.3.
Horizontal dynamics are present but largely irrelevant to the PSS
demonstration.

**[Figure 3.1: AFGL mid-latitude-summer O₃ profile interpolated to the
supercell vertical grid (the initial state qO3 produces). To be added.]**

## 3.3 The TUV-x column extension

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

The MPAS atmosphere lid for the supercell case sits at 50 km — that's
roughly stratopause level, but Chapman-cycle photolysis depends on UV
radiation that has already been attenuated by the entire ozone column
*above* the photolysis cell, including the ~50–100 km region MPAS
itself does not simulate. Without an extension, TUV-x sees vacuum
above 50 km, jO₃ and jNO₂ are off by a non-trivial factor at high
altitudes, and the Chapman steady state never establishes properly.

The fix is `micm_configs/tuvx_upper_atm.csv`: a tracked CSV carrying
temperature, air number density, and ozone number density on a
uniform 5-km grid from 50 to 100 km. The temperature and air values
come from the US Standard Atmosphere 1976 tables; the ozone values
come from the AFGL mid-latitude-summer constituent profile. At
runtime, `mpas_tuvx.F::load_extension_csv` stitches MPAS midpoint
values (lower slice) and CSV midpoint values (upper slice) into a
single radiator column for TUV-x, blending across the boundary so
the profile is continuous.

The stitch lives in `src/core_atmosphere/chemistry/mpas_tuvx.F`; for
the broader integration story, see
[TUV-x integration](../chempas/guides/TUVX_INTEGRATION.md).

## 3.4 Generating and verifying the extension CSV

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

**Generate the CSV.** The generator is parameterized but defaults to
the configuration the runtime expects (50–100 km, 10 layers, 5-km
spacing). These commands reuse the source/run variables from §2.3. In a
new shell, establish them and activate the environment first:

```bash
cd /path/to/CheMPAS-A-qualification
export CHEMPAS_ROOT="$(pwd)"
export CHEMPAS_RUN_ROOT=/path/to/CheMPAS-run-data
export CHEMPAS_TUVX_DATA=/path/to/MUSICA/configs/tuvx/data
export SUPERCELL_RUN="$CHEMPAS_RUN_ROOT/supercell"
conda activate mpas
test -d "$CHEMPAS_TUVX_DATA"

python scripts/gen_tuvx_upper_atm.py \
    --out "$SUPERCELL_RUN/tuvx_upper_atm.csv"
```

The script emits a header line followed by one row per edge with
columns `z_km, T_K, n_air_molec_cm3, n_O3_molec_cm3`. The output path
must match the `config_tuvx_extension_file` value in the namelist
(set in section 3.6 below).

**Verify the stitched column.** The companion plotter overlays the
MPAS region with the extension-CSV region as TUV-x actually sees
them, including the edge-blending the runtime applies at the 50-km
boundary:

```bash
cd "$SUPERCELL_RUN"
python "$CHEMPAS_ROOT/scripts/plot_extension_profiles.py" \
    -i output.isotherm.nc --csv tuvx_upper_atm.csv
```

This pre-run check uses the stable isotherm LNOx artifact named in Chapter 2.
After §3.6 creates the Chapman result, repeat the command with
`-i output.nc` to inspect the column from the actual Chapman run.

**[Figure 3.2: Stitched T, n_air, and n_O₃ vertical profiles from
mpas_tuvx.F. MPAS region (below 50 km) and extension-CSV region
(above 50 km) overplotted. To be added.]**

## 3.5 Initializing the Chapman tracers

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

The Chapman + NOx mechanism needs six prognostic tracers seeded with
realistic vertical profiles. These are *initial conditions only* —
the MICM solver evolves all six over the run via the Chapman cycle
plus NOx reactions:

- `qO2` — uniform 0.2313 kg/kg (the dry-air O₂ mass mixing ratio).
  Effectively constant under the run; O₂ is consumed only by
  Schumann–Runge photolysis, which is small.
- `qO3` — AFGL mid-latitude-summer profile, interpolated to the MPAS
  grid (continuous with the upper-atmosphere extension at the lid).
  Starting near the climatology avoids the months-to-years
  Chapman spin-up in the lower stratosphere.
- `qO` — an altitude-dependent Chapman quasi-steady-state seed by default;
  select `--qo-mode uniform` or `--qo-mode zero` for the alternate script
  modes. `qO1D` starts at zero. Both are fast radicals evolved by chemistry.
- `qNO`, `qNO2` — total-NOx profile (0.05 ppb tropospheric background
  → ~10 ppb stratospheric peak around 25–35 km → drop near the lid),
  partitioned ~30 % NO / 70 % NO₂ as a near-Leighton initial guess.
  The Leighton partitioning settles within seconds; the total NOx
  burden is preserved over the run.

`scripts/init_chapman.py` writes these six tracers into
`supercell_init.nc`:

```bash
cd "$SUPERCELL_RUN"
python "$CHEMPAS_ROOT/scripts/init_chapman.py" -i supercell_init.nc
```

Note: this rewrites tracers in `supercell_init.nc` in place. If
you've been running the supercell + LNOx case from Chapter 2 and
plan to switch back, copy `supercell_init.nc` aside first or be
prepared to re-run `init_atmosphere_model` to regenerate it.

## 3.6 Run with the Chapman + NOx mechanism

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

**Stage the mechanism and edit the namelist.** From the run directory:

```bash
cd "$SUPERCELL_RUN"
cp "$CHEMPAS_ROOT/micm_configs/chapman_nox.yaml" .
cp "$CHEMPAS_ROOT/micm_configs/tuvx_chapman_nox.json" .
[ -e data ] || ln -s "$CHEMPAS_TUVX_DATA" data
```

Replace the chemistry records in `$SUPERCELL_RUN/namelist.atmosphere` with
the Chapman + NOx configuration, and remove any prior `&lnox` record:

```fortran
&chemistry
    config_micm_file = 'chapman_nox.yaml'
/

&photolysis
    config_tuvx_config_file = 'tuvx_chapman_nox.json'
    config_tuvx_top_extension = .true.
    config_tuvx_upper_column_mode = 'legacy_static'
    config_tuvx_extension_file = 'tuvx_upper_atm.csv'
    config_chemistry_latitude = 35.86
    config_chemistry_longitude = -97.93
/
```

Six fields, no LNOx source terms — Chapman has no lightning channel.
The `tuvx_chapman_nox.json` photolysis configuration provides the
four rates the mechanism consumes (jO₂, jO₃→O, jO₃→O¹D, jNO₂); its
description in the JSON file says explicitly that it pairs with
`chapman_nox.yaml`.

Add the following runtime photolysis fields to
`stream_list.atmosphere.output` if they are not already present:

```text
j_jNO2
j_jO2
j_jO3_O
j_jO3_O1D
```

**Archive prior output and run.** Same pattern as the Chapter 2
supercell runs:

```bash
timestamp=$(date +%Y%m%d_%H%M%S)
[ -f output.nc ] && mv output.nc output.${timestamp}.nc
[ -f log.atmosphere.0000.out ] && \
    mv log.atmosphere.0000.out log.atmosphere.0000.${timestamp}.out

mpiexec -n 8 "$CHEMPAS_ROOT/atmosphere_model"
```

Verify the run completed cleanly by checking the tail of
`log.atmosphere.0000.out`:

```
Critical error messages = 0
```

**Plot.** `scripts/plot_chemistry_profiles.py` produces seven panels of
horizontal-mean vertical profiles with a cellwise min--max envelope:

```bash
cd "$SUPERCELL_RUN"
python "$CHEMPAS_ROOT/scripts/plot_chemistry_profiles.py" \
    -i output.nc
```

The panels are qO₃, total atomic oxygen qO + qO1D, qNO₂, and qNO,
followed by jO₂, combined jO₃ = jO₃→O + jO₃→O¹D, and jNO₂. With no
`-o` option, the command writes `plots/chemistry_profiles.png` and
`plots/chemistry_profiles.pdf`.

**[Figure 3.3: Horizontal-mean vertical profiles and cellwise min--max
envelopes for the four species panels and three combined photolysis panels,
Chapman + NOx mechanism. To be added.]**

What to look for: O₃ and NOx maxima in the seeded stratospheric
layer (~25–35 km); jNO₂ rising sharply with altitude as the column
above thins; and evolution of the qNO and qNO₂ profiles. The script does not
plot their ratio; section 3.8 checks that diagnostic analytically.

## 3.7 The photostationary-state diagnostic

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

In sunlight, the NO–NO₂–O₃ system relaxes within seconds to a steady
state where NO₂ photolysis (NO₂ + hν → NO + O, rate jNO₂) is balanced
by the reverse NO + O₃ titration. This is the **Leighton
photostationary state**:

$$
\frac{[\mathrm{NO}]}{[\mathrm{NO_2}]}
= \frac{j_{\mathrm{NO_2}}}{k_{\mathrm{NO+O_3}}\,[\mathrm{O_3}]}
$$

where the temperature-dependent reaction rate

$$
k_{\mathrm{NO+O_3}}(T)
= 1.084\times10^{6}\,\exp\!\left(-\frac{1370}{T}\right)
\;\;\text{m}^3\,\text{mol}^{-1}\,\text{s}^{-1}
$$

is the current `chapman_nox.yaml` parameterization. It is equivalent to
approximately $1.80\times10^{-12}\exp(-1370/T)$ cm³ molecule⁻¹ s⁻¹.

**The Leighton curve** is what you get when you evaluate the right-hand
side of the expression above at every level of the column: it's the
analytical [NO]/[NO₂] partitioning the simple two-reaction system
*should* settle to, given the local jNO₂ and [O₃]. Plotting the
simulated NO/NO₂ ratio alongside the Leighton curve (Figure 3.4 in
§3.8 and the bottom-left panel of the standalone column-model plot in
§3.10) is a direct visual check on the photolysis–titration balance.
Where the two curves agree, the chemistry is at PSS as expected; where
they diverge, either the system hasn't relaxed yet, or some other
reaction the simple expression doesn't capture is perturbing the
partitioning. In the current mechanism, NO₂ + O → NO + O₂ and the broader
Chapman radical chemistry are omitted from the two-reaction expression.

**Where it should hold.** In the seeded stratospheric NOx peak layer
(~25–35 km), photolysis is strong, [O₃] is high, and the partitioning
relaxation timescale is short. Simulated [NO]/[NO₂] should approach the
Leighton curve after spin-up; the additional NO₂ + O pathway and Chapman
radical chemistry can produce a real offset from the reduced expression.

**Where it shouldn't.** Near the surface in shadow or in the lowest
model layers where the photolysis driver is weak, the PSS expression
loses diagnostic value. As jNO₂ → 0 the analytical target tends to zero,
but the daytime steady-state assumptions and useful photolysis--titration
comparison disappear.
Spin-up note: 10–15 minutes of model time is plenty for partitioning
to settle in the stratospheric column.

## 3.8 Verifying numerically

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

Two complementary checks.

**Maintained checks.** First validate field presence, finiteness, and
non-negativity in the result you just produced:

```bash
cd "$SUPERCELL_RUN"
python "$CHEMPAS_ROOT/scripts/check_chem_output.py" output.nc \
  --require qO2 qO qO1D qO3 qNO qNO2 \
            j_jNO2 j_jO2 j_jO3_O j_jO3_O1D \
  --nonneg
```

From the repository root, run the Python suite and the focused chemistry
contract that exercises box, column, photolysis, NOy, radical, and Troe
behavior:

```bash
cd "$CHEMPAS_ROOT"
python -m unittest discover -v
scripts/test_global_tropo_f0.sh
```

The executable E0 suite includes a frozen 24-hour `chapman_nox_global`
artifact when its external bundle is available:

```bash
scripts/test_miem_disabled_baselines.sh . --case chapman_nox_global
```

This is a historical compatibility and bitwise-regression gate: its captured
mechanism is named `Chapman-NOx-noO1D`, omits qO1D, and has a different SHA
from the current `micm_configs/chapman_nox.yaml`. The manifest does not carry
a maintained 24-hour executable baseline for the current six-species
tutorial mechanism.

See [MVP Stage 5](../chempas/mvp/STAGE5_FULL_REGRESSION.md) for the accepted
clean build, 268-test Python run, and all 16 shell contracts.

**Analytical PSS check.** Pull jNO₂, [O₃], [NO], [NO₂] from
`output.nc` at the final timestep and compare the simulated ratio
against Leighton:

```python
import numpy as np
from netCDF4 import Dataset

# Current chapman_nox.yaml coefficient is in m3 mol-1 s-1.
A_SI, C = 1.084e6, -1370.0
M_NO, M_NO2, M_O3 = 0.030, 0.046, 0.048
P0, R_D, CP_D = 100000.0, 287.0, 1004.5

with Dataset('output.nc') as ds:
    qNO  = ds['qNO'][-1]
    qNO2 = ds['qNO2'][-1]
    qO3  = ds['qO3'][-1]
    jNO2 = ds['j_jNO2'][-1]
    rho = ds['rho'][-1]
    pressure = ds['pressure'][-1]
    theta = ds['theta'][-1]
    zgrid = np.asarray(ds['zgrid'][:])

if zgrid.ndim == 3:       # tolerate time-dependent or static zgrid output
    zgrid = zgrid[-1]
z_mid = 0.5 * (zgrid[:, :-1] + zgrid[:, 1:])
temperature = theta * (pressure / P0) ** (R_D / CP_D)
k_NO_O3 = A_SI * np.exp(C / temperature)
o3_mol_m3 = qO3 * rho / M_O3

# Convert the mass-mixing-ratio partition to a molecular abundance ratio.
sim = (qNO / M_NO) / np.maximum(qNO2 / M_NO2, 1.0e-30)
leighton = jNO2 / np.maximum(k_NO_O3 * o3_mol_m3, 1.0e-30)
mask = ((z_mid >= 25_000.0) & (z_mid <= 35_000.0) &
        (jNO2 > 0.0) & np.isfinite(sim) & np.isfinite(leighton))
print('median ratio agreement (sim / Leighton), 25-35 km:',
      float(np.median((sim / leighton)[mask])))
```

The reported ratio should be finite and near unity in the sunlit 25–35 km
layer. Treat this as a physics diagnostic, not the bitwise acceptance gate:
the full mechanism contains the NO₂ + O pathway and Chapman radical
chemistry omitted from the two-reaction Leighton expression. The maintained
regression contracts above provide the release qualification.

**[Figure 3.4: Simulated vs. analytical Leighton [NO]/[NO₂] ratio vs.
height at the final timestep. To be added.]**

## 3.9 Next steps

```{admonition} Draft - revisions in progress
:class: warning

This section is being revised.
```

- **The MUSICA/MICM coupling internals** are documented in
  [MUSICA integration](../chempas/musica/MUSICA_INTEGRATION.md).
- **TUV-x integration engineering** (the integration story behind
  `mpas_tuvx.F` and the column extension) is documented in
  [TUV-x integration](../chempas/guides/TUVX_INTEGRATION.md).
- **Upstream MUSICA, MICM, and TUV-x docs** are linked from the
  [project landing page](../index.rst) in the *See also* section.
- **The next chapter** is
  [Stratosphere — Chapman + NOx (Global)](04-stratosphere.md) — the same
  chemistry on the `x1.40962` global mesh, where the day–night
  photolysis terminator and zonal-mean ozone response become visible.
- **Further idealized cases** (mountain wave, chem box) will be added
  when their tutorial chapters are written. *(Not yet scheduled.)*

## 3.10 Standalone Chapman + NOx column model

The standalone counterpart of this whole chapter — same
`chapman_nox.yaml` MICM mechanism, TUV-x photolysis on a vertical
column, no MPAS in the loop. `scripts/musica_python/chapman_nox_column.py`
loads MUSICA's bundled `vTS1` TUV-x calculator (which provides jO₂,
jO₃→O, jO₃→O¹D, jNO₂), maps its TS1 reaction labels to
`chapman_nox.yaml`'s `PHOTO.*` parameter names via a small alias table
in the script, and runs a 12-hour diurnal cycle starting at 06:00
local at the supercell case's nominal lat/lon (Norman, OK). The
column grid is whatever vTS1 dictates — independent of the MPAS mesh
and of the upper-atmosphere extension introduced in §3.3.

Initial profiles come from `scripts/init_chapman.py`'s helpers (AFGL
mid-latitude-summer O₃, total NOx with daytime 30/70 NO/NO₂
partitioning), so the standalone column shares the coupled run's O₃ and NOx
profiles. It is not an identical initial state: the standalone script starts
O and O¹D at zero, whereas `init_chapman.py` seeds qO from its
altitude-dependent quasi-steady-state mode by default and starts qO1D at
zero.

Pre-req: see Chapter 1's [Python environment for standalone
examples](01-overview.md) section.

Run:

```bash
cd "$CHEMPAS_ROOT"
python scripts/musica_python/chapman_nox_column.py
```

The script writes `scripts/musica_python/chapman_nox_column.nc` and
`scripts/musica_python/chapman_nox_column.png`. The generated PNG contains
the solar-noon O₃ and NOx profiles, the simulated-versus-Leighton comparison,
and O₃ time series at three representative altitudes; it is not a tracked
tutorial asset.

What to look for: the simulated NO/NO₂ ratio in the stratospheric column
tracks the plotted Leighton curve qualitatively. One current-script caveat is
important: MICM uses the current YAML coefficient
$1.084\times10^6\exp(-1370/T)$ m³ mol⁻¹ s⁻¹, but the dashed diagnostic in
`chapman_nox_column.py` still uses the legacy
$1.7\times10^{-12}\exp(-1310/T)$ cm³ molecule⁻¹ s⁻¹. A roughly factor-1.3
offset therefore combines that coefficient mismatch with the additional
NO₂ + O pathway and Chapman radical chemistry; it cannot be attributed only
to O/O¹D coupling. The O₃ mixing-ratio profile peaks at ~6 ppm near
~42 km (consistent with the AFGL mid-latitude-summer
climatology used by `init_chapman.py`; tropical and US-standard
profiles peak higher, closer to 8–10 ppm). The O₃ *number-density*
peak sits lower in the column, near ~20 km, because air density
falls off faster than mixing ratio rises — a classic stratospheric
O₃ feature. The script selects `datetime.now(TZ).date()` and runs from 06:00
local for 12 hours, so the solar-zenith range and O₃ swing vary with the date
of invocation; near-solstice values are illustrative, not invariant expected
output. This provides an independent numerical check on the same mechanism
the chapter's MPAS-coupled run exercises.
