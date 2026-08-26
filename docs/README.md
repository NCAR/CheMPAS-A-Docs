# Building the Documentation

CheMPAS-A uses Sphinx, MyST Parser, and the Read the Docs theme. The public
deployment source is `NCAR/CheMPAS-A-Docs`; `.readthedocs.yaml` and `docs/`
are mirrored from the development repository without removing the canonical
copies there. Run all commands below from either repository root.

Install the documentation dependencies in the active Python environment:

```bash
python -m pip install -r docs/requirements.txt
```

Build the HTML documentation with warnings treated as errors:

```bash
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

Check links with the same warning policy:

```bash
python -m sphinx -W --keep-going -b linkcheck docs docs/_build/linkcheck
```

The documentation source is self-contained. Public source and example links
target the tagged CheMPAS-A MVP and its wiki, so all external links remain part
of the warning-fatal check.

The `-W` option turns warnings into build failures, while `--keep-going`
reports all warnings in one run. Read the Docs applies the same warning-fatal
policy through `.readthedocs.yaml`.

The generated HTML starts at `docs/_build/html/index.html`. Build products
under `docs/_build/` are excluded from the Sphinx source tree and should not
be committed.
