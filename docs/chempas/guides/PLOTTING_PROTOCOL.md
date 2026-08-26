# CheMPAS-A Scientific Plotting Protocol

**Protocol version:** `chempas-science-plot-v1`

This protocol defines the semantic and visual requirements for verified
CheMPAS-A scientific figures. `scripts/style.py` remains the implementation
source for fonts, colors, chemical notation, and reusable heading helpers.
Case-specific plotters may choose layouts appropriate to their evidence, but
must preserve the hierarchy and quantity definitions below.

## Figure hierarchy

Every verified scientific figure must contain, in order:

1. A concise figure title in Title Case. Preserve accepted capitalization for
   acronyms, mechanism names, and chemical formulas.
2. A subtitle stating the experiment or gate, temporal context, spatial or
   vertical domain, and comparison when those concepts apply.
3. Lettered panel titles in sentence case: `(a)`, `(b)`, and so on.
4. Axis, colorbar, and legend labels that define the plotted quantity and unit
   without relying on the surrounding prose.

Use `style.apply_figure_heading()` and `style.panel_heading()` so the subtitle
is visually subordinate and chemical formulas are formatted consistently.
`style.figure_heading()` remains the validation/formatting primitive used by
the figure helper. Numerical acceptance residuals belong in an annotation,
legend, or caption rather than in the primary title.

## Time context

- A time-series figure must state its inclusive start and end timestamps in
  UTC, even when the x-axis uses elapsed time.
- A snapshot map must state its valid UTC timestamp. If it represents the end
  of an experiment, the subtitle must also identify the experiment or gate.
- A final history record is an instantaneous snapshot, even when it follows a
  24-hour simulation. Label a field as a daily or interval mean only after an
  explicit time-weighted average over the stated interval has been computed.
- An accumulated quantity must state its integration interval or date range.
- Inventory interpolation figures must state the source brackets and sampled
  or valid time.
- Use unambiguous ISO-like timestamps: `2024-07-01 00:00–2024-07-02 00:00 UTC`.

## Quantity and comparison semantics

- Distinguish an absolute state from a perturbation. Name the physical
  intervention and its time window, for example `emissions applied`, `emissions
  withheld during analysis`, or `emissions continued − emissions withheld`.
  Do not use generic implementation terms such as `enabled`, `disabled`, or
  unqualified `control` in public figure text. Do not use `forcing` as a
  synonym for emissions because it is easily confused with radiative forcing.
- Distinguish instantaneous flux, time-integrated source, mixing ratio, number
  density, layer burden, column burden, and global burden.
- Every column quantity must state its vertical domain. For the global
  tropospheric NOx ladder, use `diagnostic troposphere (p ≥ 150 hPa)`; use
  `full model column` only for explicitly unqualified stability diagnostics.
- Individual species burdens use moles of that species. Nitrogen-family
  burdens use moles of N and must state the family definition.
- Paired-branch science figures must show the reference branch or the explicit
  branch difference. An absolute emissions-branch field alone is insufficient
  evidence of an emissions response. State inherited emissions or a shared
  spin-up so the reference branch is not mistaken for a pristine atmosphere.
- A global NO/NO2 experiment must include both NO and NO2 tropospheric column
  burdens. Family closure alone does not expose photochemical partitioning.

## Plot selection and ordering

Primary science figures should establish the narrative in this order:

1. emissions or another source;
2. absolute atmospheric state;
3. explicit emissions-minus-reference difference;
4. chemical partitioning and evolution; and
5. vertical structure.

Budget closure, concentration plausibility, restart equivalence, performance,
memory, and output volume are verification or engineering figures. Retain them
as supplemental evidence, but do not substitute them for the primary species
state and response figures.

## Scales, coordinates, and color

- Positive quantities use a sequential map and a linear or logarithmic scale
  appropriate to their dynamic range.
- Signed differences use a diverging map centered exactly on zero. Symmetric
  limits are mandatory; tick labels around the linear threshold must remain
  legible and must include a single explicit zero.
- If robust percentiles set map limits, use colorbar extensions and document
  the percentile in the plotter or manifest. Exact extrema remain available in
  machine-readable evidence.
- Pressure coordinates decrease upward. With shared axes, invert or set the
  pressure limits exactly once.
- Geographic maps state longitude and latitude units. Add geographic context
  when supported without changing or interpolating the verified native-grid
  values.
- A species has one stable color within a figure bundle. Line style, rather
  than a second unrelated color, distinguishes the emissions and reference
  branches.

## Typography and chemistry notation

- Use the NCAR font and size presets from `scripts/style.py`; never hardcode
  font sizes in an individual panel.
- Use `style.species_label()` and `style.format_title()` for chemical formulas
  and families.
- Put units in square brackets. Use SI units and explicit powers, for example
  `mmol N m⁻²`, `kg m⁻² s⁻¹`, `ppb`, or `molecule cm⁻³`.
- Legends use concise nouns and state comparison semantics. Avoid repeating
  the complete title in every legend entry.

## Verified output and provenance

- Produce at least 300-dpi PNG and vector PDF versions.
- Rasterize dense native-grid artists in the PDF while retaining vector text,
  axes, and legends.
- Plot only passed, promotable evidence and verify every supplied history by
  size and SHA-256 before reading it.
- The figure manifest must record this protocol version and the SHA-256 of this
  document, the style module, plotter, schemas, reports, selected histories,
  and rendered files.
- A plotting change invalidates the prior figure hashes. Regenerate and
  revalidate the entire affected bundle before publication.

## Global tropospheric NOx bundle

For the R3/F3 ladder, the primary bundle must include:

- NO and NO2 surface-emission fluxes;
- reduced R3 emissions-applied and emissions-applied-minus-withheld NO/NO2
  diagnostic-tropospheric column burdens;
- expanded F3 emissions-continued and emissions-continued-minus-withheld NO/NO2
  diagnostic-tropospheric column burdens;
- hourly emissions/reference and emissions-minus-reference NO/NO2 burden
  histories;
- expanded HNO3/NOy partitioning and O3/HOx response; and
- vertical response with the 150 hPa diagnostic boundary.

Family-budget closure, concentration ranges, and resource use remain required
supplemental evidence.

R3 begins from a nonzero atmospheric NOx state; its reference branch withholds
CAMS-NOx emissions only during the analysis interval. F3 branches all inherit
the same FS restart produced with CAMS-NOx emissions, after which the reference
branch withholds those emissions during F3. Thus F3 differences diagnose the
marginal effect of continuing the emissions through the analysis day, not an
emitting atmosphere versus a pristine or never-emitted atmosphere.
