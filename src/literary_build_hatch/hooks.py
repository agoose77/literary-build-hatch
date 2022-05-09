from hatchling.plugin import hookimpl

from .plugin import LiteraryBuildHook


@hookimpl
def hatch_register_build_hook():
    return LiteraryBuildHook
