---
description: Set up the development environment with miniforge and uv
allowed-tools: Bash(uv *) Bash(curl *) Bash(pip install uv) Bash(conda *)
---

# /dev-setup

Set up a local development environment.

1. Create a miniforge environment:

   ```bash
   conda create -n dppvalidator python=3.12 -y && conda activate dppvalidator
   ```

1. Install the `uv` package manager (skip if already installed):

   ```!
   command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Alternative: `pip install uv`

1. Install project dependencies:

   ```!
   uv sync --dev
   ```

1. Install pre-commit hooks:

   ```!
   uv run pre-commit install
   ```

1. Verify installation:

   ```!
   uv run python -c "import dppvalidator; print('Setup complete!')"
   ```

After setup, run `/lint` and `/test` to verify everything works.
