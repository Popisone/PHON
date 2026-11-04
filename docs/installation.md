# Installation

## Prerequisites

- Python 3.10 - 3.14
- pip
- git

## Windows

```powershell
git clone https://github.com/Popisone/PHON.git
cd PHON
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
phon --version
```

## Linux / macOS

```bash
git clone https://github.com/Popisone/PHON.git
cd PHON
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
phon --version
```

## From PyPI

```bash
pip install phon
```

## Optional extras

| Feature | Command |
|---|---|
| GDSII export | `pip install gdstk` |
| JAX autodiff | `pip install jax jaxlib optax` |
| ML benchmarks | `pip install scikit-learn scipy` |

## Troubleshooting

**`phon: command not found`** -- activate the virtual environment first.

**`ModuleNotFoundError: phon`** -- reinstall: `pip install -e .`

**Tests fail** -- run `pytest tests/ -q` and open an issue on GitHub.
