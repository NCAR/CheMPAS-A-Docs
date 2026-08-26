CheMPAS-A Developer Notes
=========================

Architecture notes, integration and usage guides, implementation records,
and reproducibility evidence for the CheMPAS-A 26.08 MVP release candidate.

The public model source is the immutable
`v2026.08.01-rc2 tag <https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01-rc2>`_.
Runnable declarative examples are maintained in the
`CheMPAS-A wiki <https://github.com/NCAR/CheMPAS-A/wiki>`_. Qualification
records may name development-only automation that is retained as provenance
but is not shipped in the public MVP repository.

.. toctree::
   :titlesonly:
   :caption: Overview

   README

.. toctree::
   :titlesonly:
   :caption: Architecture And Integration

   architecture/ARCHITECTURE
   architecture/COMPONENTS

.. toctree::
   :titlesonly:
   :caption: Chemistry, Emissions, And Photolysis

   musica/MUSICA_INTEGRATION
   musica/MUSICA_API
   musica/MIEM_INTEGRATION
   musica/MIEM_SCALABILITY_DESIGN
   musica/GLOBAL_TROPOSPHERIC_NOX
   musica/GLOBAL_TROPOSPHERIC_METHANE
   guides/TUVX_INTEGRATION
   guides/LNOX_INTEGRATION
   guides/VISUALIZE
   guides/PLOTTING_PROTOCOL

.. toctree::
   :titlesonly:
   :caption: Implementation Records

   CHEM_TRACER_OUTPUT_UNITS_PLAN
   MIEM_IMPLEMENTATION_LOG
   mvp/PLAN_EMISSIONS
   mvp/PLAN_GLOBAL_TROPOSPHERIC_NOX
   mvp/PLAN_GLOBAL_TROPOSPHERIC_METHANE

.. toctree::
   :titlesonly:
   :caption: MVP Qualification

   mvp/MVP_PRE_RELEASE
   mvp/STAGE0_DATA_CONTRACT
   mvp/STAGE1_PRESCRIBED_O3
   mvp/STAGE2_EMISSIONS
   mvp/STAGE3_LOCAL_QUALIFICATION
   mvp/STAGE4_GLOBAL_LADDER
   mvp/STAGE5_FULL_REGRESSION
   mvp/STAGE6_PRE_RELEASE

.. toctree::
   :titlesonly:
   :caption: Validation Evidence

   results/TEST_RUNS
   musica/benchmarks/README
   musica/global-runs/stage9a-inventory-qualification
   musica/global-runs/stage9b-inventory-qualification
   musica/global-tropo-runs/README
   musica/global-methane-runs/stage0-baseline
   musica/global-methane-runs/d0-data-access-status
   musica/global-methane-runs/implementation-verification

.. toctree::
   :titlesonly:
   :caption: Historical Baseline

   upstream/2026-04-19-vs-mpas-v8.3.1
