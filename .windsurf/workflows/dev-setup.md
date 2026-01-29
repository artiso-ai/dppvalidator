---
description: Set up development environment with miniforge and uv
---

1. Create miniforge environment:
   `conda create -n dppvalidator python=3.12 -y && conda activate dppvalidator`

2. Install uv package manager:
   // turbo
   `curl -LsSf https://astral.sh/uv/install.sh | sh`

   Or using pip: `pip install uv`

3. Install project dependencies:
   // turbo
   `uv sync --dev`

4. Install pre-commit hooks:
   // turbo
   `uv run pre-commit install`

5. Verify installation:
   // turbo
   `uv run python -c "import dppvalidator; print('Setup complete!')"`

**Post-setup**: Run `/lint` and `/test` to verify everything works.
