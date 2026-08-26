# CheMPAS-A Documentation

This public repository is the deployment source for the
[CheMPAS-A documentation](https://chempas-a.readthedocs.io/). It describes the
CheMPAS-A 26.08 Minimum Viable Product release candidate:

- model source: [`v2026.08.01-rc2`](https://github.com/NCAR/CheMPAS-A/tree/v2026.08.01-rc2)
  (`5acca0227088d9e6e4c58764574b695956a7a804`)
- documentation source snapshot: `44ee78c5f730ad3bebb0116864e5f8772297896c`
- public examples and input contracts: [CheMPAS-A wiki](https://github.com/NCAR/CheMPAS-A/wiki)

The canonical `.readthedocs.yaml` and `docs/` sources are maintained in the
CheMPAS-A development repository and mirrored here for public deployment; the
canonical copies are not removed from that repository. Small files under
`docs/_downloads/` make the Sphinx tree independently buildable and preserve
the provenance of referenced qualification inputs.

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
