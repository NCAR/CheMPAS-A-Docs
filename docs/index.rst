CheMPAS-A
=========

.. |logo_uarizona| image:: _static/logo_uarizona.svg
   :height: 78px
   :alt: University of Arizona

.. |logo_ncar| image:: _static/logo_nsf_ncar_ucar.svg
   :height: 86px
   :alt: NSF NCAR | UCAR

.. rst-class:: funding-logos

|logo_ncar| |logo_uarizona|

CheMPAS-A (Chemistry for MPAS - Atmosphere) is an ACOM integration pilot that
couples MUSICA/MICM atmospheric chemistry to MPAS-Atmosphere on its native
unstructured Voronoi mesh, developed as part of the NSF CSSI project QUACS
(Quick Updates to Aerosol and Chemistry Systems for Next Generation Multi-Scale
Models). This site documents the CheMPAS-A 26.08 Minimum Viable Product (MVP)
release candidate, based on MPAS-Model v8.4.1.

**MVP source:** `v2026.08.01-rc2 <https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01-rc2>`_
(``5acca0227088d9e6e4c58764574b695956a7a804``)

**Runnable examples and input contracts:** `CheMPAS-A wiki <https://github.com/NCAR/CheMPAS-A/wiki>`_

**Contributors:** David Fillmore (NCAR ACOM), Gabriele Pfister (NCAR ACOM),
Avelino Arellano (University of Arizona); Mary Barth (NCAR ACOM),
Matt Dawson (Cohere Consulting, LLC), Michael Duda (NCAR MMM), Jiwon Gim (NCAR ACOM),
Rajesh Kumar (NCAR RAL), Forrest Lacey (NCAR RAL), Scott Meech (NCAR RAL),
Kyle Shores (NCAR ACOM), Katherine Thayer-Calder (NCAR CGD),
Victor Weeks (NCAR RAL).

**Funding.** This work is supported by the U.S. National Science Foundation
through the Cyberinfrastructure for Sustained Scientific Innovation (CSSI)
program, project *QUACS: Quick Updates to Aerosol and Chemistry Systems for
Next Generation Multi-Scale Models*
(`NSF Award #2513280 <https://www.nsf.gov/awardsearch/show-award/?AWD_ID=2513280&HistoricalAwards=false>`_;
PI: Avelino Arellano, University of Arizona; Co-PI: Gabriele Pfister,
NSF NCAR ACOM).

.. note::

   This documentation describes the process-integration MVP at the immutable
   tag linked above. The reduced mechanisms and example initial conditions are
   research demonstrations, not a production air-quality configuration. The
   public wiki is the supported source for declarative example inputs; detailed
   qualification records in these pages preserve how the MVP was produced but
   may name development-only automation that is not shipped in the MVP source
   repository.

The CheMPAS-A MVP demonstrates runtime tracer allocation,
MUSICA/MICM state transfer, TUV-x photolysis and prescribed upper-column
fields, selected-cell MIEM offline emissions, and idealized through global
chemistry qualification workflows.

CheMPAS-A uses calendar versioning (YY.MM), tracked independently from the
MPAS base model version. This documentation includes an MPAS-Atmosphere
User's Guide adapted from the MPAS v8.4.1 release with CheMPAS-A-specific
chemistry chapters and namelist entries; a CheMPAS-A tutorial and developer
notes; and a lightly edited port of the MPAS-Atmosphere Technical
Description from the v8 NCAR Technical Note draft for the dynamical core,
equations, and spatial discretization.

.. admonition:: Under construction
   :class: warning

   These docs are an active port and are not yet feature-complete. In
   particular, figures from the MPAS-Atmosphere User's Guide and Technical
   Description still need to be regenerated — placeholders of the form
   ``**[Figure N.M: caption. To be added next session.]**`` mark the
   intended location of each figure in the Technical Description, and
   figure references in the User's Guide (e.g., Figure 9.1, the vertical
   grid schematics in Appendix C) currently render without their source
   images.

.. seealso::

   `MUSICA documentation <https://musica.readthedocs.io/>`_ —
   **MUSICA** (Multi-Scale Infrastructure for Chemistry and Aerosols):
   the project umbrella, MUSICA-Fortran build instructions, and
   overall chemistry-coupling guidance.

   `MICM documentation <https://micm.readthedocs.io/>`_ —
   **MICM** (Model-Independent Chemistry Module): the chemistry
   solver. Covers mechanism authoring (YAML configs), solver families
   (Rosenbrock, Backward Euler, etc.), rate-constant forms, and
   tolerance / sub-stepping controls.

   `MIEM documentation <https://miem.readthedocs.io/>`_ —
   **MIEM** (Model-Independent Emissions Module): the compiled C++20
   offline-emissions library. CheMPAS-A uses its revision-qualified extended
   Fortran binding through MUSICA; see the developer API pages for the exact
   pin-versus-``main`` boundary.

   `TUV-x documentation <https://tuv-x.readthedocs.io/>`_ —
   **TUV-x** (Tropospheric Ultraviolet and Visible, eXtended): the
   photolysis solver. Covers wavelength grids, cross sections and
   quantum yields, cloud radiator inputs, and the JSON configuration
   format.

   CheMPAS-A is a downstream consumer of all three; the runtime
   species list, rate constants, and photolysis rates come from the
   MICM and TUV-x configurations loaded at startup.

.. toctree::
   :maxdepth: 3

   README
   users-guide/index
   tutorial/index
   technical-description/index
   chempas/index
