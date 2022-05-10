import os
import pathlib
import shutil

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from literary.core.config import find_project_config, load_project_config
from literary.core.package import PackageBuilder


class LiteraryBuildHook(BuildHookInterface):
    PLUGIN_NAME = 'literary'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Find literary config file
        root_path = pathlib.Path(self.root)
        config_path = find_project_config(root_path)
        if config_path.parent != root_path:
            raise RuntimeError("missing literary config")

        config = load_project_config(config_path)

        # Build Python files
        self._builder = PackageBuilder(config=config)

        # Ensure that we own build directory
        if self._builder.generated_path == root_path:
            raise RuntimeError("cannot generate inside root")

    def initialize(self, version, build_data):
        if self.target_name != 'wheel':
            return

        self._builder.build()

        # Ensure generated files are included in wheel
        build_data["force-include"] = {self._builder.generated_path: "/"}

    def clean(self, versions):
        # Remove contents of generated directory
        for path in self._builder.generated_path.iterdir():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                os.unlink(path)
