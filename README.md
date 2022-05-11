# literary-build-hatch
[![pypi-badge][]][pypi]

[pypi-badge]: https://img.shields.io/pypi/v/literary-build-hatch
[pypi]: https://pypi.org/project/literary-build-hatch

A hatch plugin to build wheels from Literary projects.

Example `pyproject.toml`:
```toml

# Include the generated lib contents in the package root
[tool.hatch.build.targets.wheel.force-include]
"lib" = "/"

# Alternatively pick up lib if it's not excluded by VCS
[tool.hatch.build]
sources = ["lib"]

# Use Literary build hook
[tool.hatch.build.targets.wheel.hooks.literary]
dependencies = ["literary-build-hatch>=0.2.0a0"]

# Specify Hatch build-system
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

This hook supports editable installs, so `pdm install` just works out of the box!
