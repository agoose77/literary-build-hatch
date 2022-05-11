import fnmatch
import os
import pathlib
import shutil
import tempfile
import zipfile

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from literary.commands.build import LiteraryBuildApp
from literary.config import find_literary_config, load_literary_config


def mangle_attribute(cls, name):
    return f"_{cls.__name__}__{name}"


class LiteraryBuildHook(BuildHookInterface):
    PLUGIN_NAME = 'literary'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Find literary config file
        root_path = pathlib.Path(self.root)
        config_path = find_literary_config(root_path)
        if config_path.parent != root_path:
            raise RuntimeError("missing literary config")

        # Build Python files
        self._builder = LiteraryBuildApp(config_file=config_path)

        # Ensure that we own build directory
        if self._builder.generated_path == root_path:
            raise RuntimeError("cannot generate inside root")

        # Store original wheel metadata constructor
        self._build_config = getattr(
            self, mangle_attribute(BuildHookInterface, "build_config")
        )
        self._metadata_constructor = self._build_config.core_metadata_constructor

    def _patch_jupyter_path(self):
        # The PEP517 isolated builder partially emulates a virtualenv
        # Jupyter gets confused about this
        jupyter_prefix = os.path.dirname(os.path.dirname(shutil.which("jupyter")))
        paths = [
            os.path.join(jupyter_prefix, "share", "jupyter"),
            *os.environ.get('JUPYTER_PATH', '').split(os.path.pathsep),
        ]
        os.environ['JUPYTER_PATH'] = os.path.pathsep.join([p for p in paths if p])

    def _require_packages(self, packages):
        # Patch metadata constructor
        def core_metadata_constructor(metadata, extra_dependencies=()):
            return self._metadata_constructor(
                metadata, tuple(extra_dependencies) + tuple(packages)
            )

        setattr(
            self._build_config,
            mangle_attribute(type(self._build_config), "core_metadata_constructor"),
            core_metadata_constructor,
        )

    def initialize(self, version, build_data):
        if self.target_name == "wheel":
            # For editable wheels, we don't want to build anything for Literary
            # Instead, we just want to patch the final wheel to support the import hook
            if version == "editable":
                if self.metadata.core.name == "literary":
                    raise RuntimeError(
                        "Cannot build an editable wheel for literary (this breaks bootstrapping)"
                    )

                self._require_packages(("literary>=4.0.0a0",))

            # We only want to generate files for standard wheels
            elif version == "standard":
                self._builder.start()

    def clean(self, versions):
        if hasattr(self._builder, "clean"):
            self._builder.clean()
