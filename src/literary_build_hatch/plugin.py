import os
import pathlib
import shutil
import tempfile

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from literary.commands.build import LiteraryBuildApp
from literary.config import find_literary_config, load_literary_config

OLDEST_LITERARY_VERSION = "literary>=4.0"


def patch_jupyter_path():
    # The PEP517 isolated builder partially emulates a virtualenv
    # Jupyter gets confused about this
    jupyter_prefix = os.path.dirname(os.path.dirname(shutil.which("jupyter")))
    paths = [
        os.path.join(jupyter_prefix, "share", "jupyter"),
        *os.environ.get('JUPYTER_PATH', '').split(os.path.pathsep),
    ]
    os.environ['JUPYTER_PATH'] = os.path.pathsep.join([p for p in paths if p])


class LiteraryBuildHook(BuildHookInterface):
    PLUGIN_NAME = 'literary'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fix PEP517 support
        patch_jupyter_path()

        # Find literary config file
        root_path = pathlib.Path(self.root)
        config_path = find_literary_config(root_path)
        if config_path.parent != root_path:
            raise RuntimeError(
                f"Could not find a Literary config file between {root_path.root} and {root_path}. "
                f"This file is required to instruct Literary on how to build this package. "
                f"See https://github.com/agoose77/literary/wiki/Configuration for more information."
            )

        # Configure builder
        self._builder = LiteraryBuildApp.instance(config_file=config_path)
        # Load configuration from file
        self._builder.load_app_config_file()

        # Ensure that we own build directory
        if self._builder.generated_path == root_path:
            raise RuntimeError(
                f"Literary is strongly opinionated about building into its own directory e.g. lib/. "
                f"This makes it easier to reason about cleaning up files. You are trying to build "
                f"directly into the root path {root_path} of this package, which is not allowed. "
                f"See https://github.com/agoose77/literary/wiki/Configuration for the destination "
                f"directory option."
            )

    def initialize(self, version, build_data):
        if self.target_name != "wheel":
            return

        # For editable wheels, we don't want to build anything for Literary
        # Instead, we just want to patch the final wheel to support the import hook
        if version == "editable":
            if self.metadata.core.name == "literary":
                raise RuntimeError(
                    "Cannot build an editable wheel for literary (this breaks bootstrapping). "
                    "If you are seeing this and don't know what it means, are you trying to "
                    "build a package called 'literary'? If so, that package name is reserved. "
                )

            # We need Literary to be able to import this package, and there may be several
            # editable packages in the current environment. This version needs to be
            # permissive as possible, so a lower bound can be manually tweaked
            build_data['dependencies'].append(OLDEST_LITERARY_VERSION)

            # Automatically add .pth file. The builder may do this too if the user specifies a directory
            # but the site module will deduplicate it
            editable_pth_name = (
                f"{self.metadata.core.name.replace('-', '_')}-literary.pth"
            )
            fd, path = tempfile.mkstemp(text=True)
            with os.fdopen(fd, 'w') as f:
                f.write(str(self._builder.packages_path))
            build_data['force_include_editable'][path] = editable_pth_name

        # We only want to generate files for standard wheels
        elif version == "standard":
            self._builder.start()

            # Include generated artifacts. N.B. This can also be done with `artifacts` and `sources`
            # But this option let's us do this on the builder side
            build_data["force_include"] = {self._builder.generated_path: "/"}

    def clean(self, versions):
        if hasattr(self._builder, "clean"):
            self._builder.clean()
