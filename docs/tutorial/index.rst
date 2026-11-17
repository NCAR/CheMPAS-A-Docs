CheMPAS-A Tutorial
==================

A hands-on walkthrough of CheMPAS-A's idealized chemistry test cases. This
tutorial complements the imported MPAS-Atmosphere User's Guide (which is a
CheMPAS-A adaptation of the upstream MPAS v8.4.1 reference documentation) with
worked examples specific to CheMPAS-A's MUSICA/MICM coupling.

Commands assume a checkout of the CheMPAS-A
`v2026.08.01 release <https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01>`_,
which carries the initialization scripts and container runner. Clone the wiki
for the public namelists, streams, mechanisms, and input contracts maintained in the
`CheMPAS-A wiki <https://github.com/NCAR/CheMPAS-A/wiki/Examples>`_.
The workflows below follow those wiki instructions; the numbered chapters
provide longer teaching examples and analysis.

.. admonition:: Work in progress
   :class: warning

   Chapters 2--4 remain in active revision. Sections and figures explicitly
   marked draft or "To be added" are provisional; documented current
   limitations are called out inline.

.. toctree::
   :maxdepth: 2
   :caption: Public Example Workflows

   running-examples
   docker

.. toctree::
   :maxdepth: 2
   :caption: Chapters

   01-overview
   02-deep-convection
   03-chapman-nox
   04-stratosphere
