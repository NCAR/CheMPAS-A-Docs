# CheMPAS-A Documentation

This public repository is the deployment source for the
[CheMPAS-A documentation](https://chempas-a.readthedocs.io/). It describes the
CheMPAS-A 26.08 Minimum Viable Product release:

- model source: [`v2026.08.01`](https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01)
  (`a76dd8ae2adce569c45433a53503a6f3c791f325`)
- documentation source snapshot: `026ad313c4ba498fb74a468972597e69a4a146f0`
- public examples and input contracts: [CheMPAS-A wiki](https://github.com/NCAR/CheMPAS-A/wiki)

The canonical `.readthedocs.yaml` and `docs/` sources are maintained in the
CheMPAS-A development repository and mirrored here for public deployment; the
canonical copies are not removed from that repository. The mirror carries only
the published documentation: paths excluded from the Sphinx build in
`docs/conf.py` stay in the development repository. Small files under
`docs/_downloads/` make the Sphinx tree independently buildable.

## Build Locally

```bash
python -m pip install -r docs/requirements.txt
python -m sphinx -W --keep-going -b html docs docs/_build/html
python -m sphinx -W --keep-going -b linkcheck docs docs/_build/linkcheck
```

The HTML entry point is `docs/_build/html/index.html`. Build products are not
committed.

## Read the Docs Deployment

The Read the Docs project slug `chempas-a` must use:

- repository URL: `https://github.com/NCAR/CheMPAS-A-Docs`
- default branch: `main`
- configuration file: `.readthedocs.yaml`

After changing the repository or branch in the Read the Docs project settings,
resynchronize the project's versions and rebuild `latest`. Subsequent pushes to
`main` should build through the repository integration.

See [LICENSE](LICENSE) for the project license.
