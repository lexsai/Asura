"""This module collects plugins from the plugins folder."""

import os
from importlib import util
from importlib.machinery import ModuleSpec
from importlib.abc import Loader
from types import ModuleType
from typing import TypeVar, Generic

PluginTypeT = TypeVar('PluginTypeT', bound='Plugin')

class Plugin(Generic[PluginTypeT]):
    """
    Collects the plugins that subclass this class into a list.
    """
    plugins: list[PluginTypeT] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)

dirpath = os.path.dirname(os.path.abspath(__file__))

def load_module(path: str) -> ModuleType:
    """
    Load a python module from the filepath.
    """
    name = os.path.split(path)[-1]
    spec = util.spec_from_file_location(name, path)

    assert isinstance(spec, ModuleSpec)

    module = util.module_from_spec(spec)

    assert isinstance(spec.loader, Loader)

    spec.loader.exec_module(module)
    return module

for fname in os.listdir(dirpath):
    if fname != 'plugin.py' and not fname.startswith('.') and \
       not fname.startswith('__') and fname.endswith('.py'):
        load_module(os.path.join(dirpath, fname))
