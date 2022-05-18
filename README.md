# literary-build-hatch
[![pypi-badge][]][pypi]

[pypi-badge]: https://img.shields.io/pypi/v/literary-build-hatch
[pypi]: https://pypi.org/project/literary-build-hatch

A hatch plugin to build wheels from Literary projects.

Example `pyproject.toml`:
```toml
[tool.hatch.build]
# Ensure lib is ignored so that these files *never* get accidentally included
excluded = ["src", "lib"]

[tool.hatch.build.targets.wheel.hooks.literary]
dependencies = ["literary-build-hatch>=0.3.0"]

[build-system]
requires = ["hatchling>=1.0.0"]
build-backend = "hatchling.build"
```

This hook supports editable installs, so `pdm install` just works out of the box!

## Details
The Hatch build plugin makes the following decisions:
- Anything in the builder `generated_path` is added to the built wheel
- The builder `generated_path` is added to `sys.path` for editable wheels
- Literary version `>=4.0.0` is required by editable wheel

The builder users `force_include` for standard wheels, meaning that the exclusion mechanism provided by hatch will be ignored for generated assets. You should use the Literary configuration to specify files that should not end up in the build directory.
