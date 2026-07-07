import os
import importlib
import inspect

from importlib.resources import files

from modules.base import BaseModule

MODULES_DIR_NAME = "modules"
MODULES = []

def load():
    try:
        modules_package = files(MODULES_DIR_NAME)
    except Exception:
        return

    module_dirs = []

    for item in modules_package.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            module_dirs.append(item.name)

    for module_dir in module_dirs:
        try:
            module = importlib.import_module(f"{MODULES_DIR_NAME}.{module_dir}.main")
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseModule) and obj is not BaseModule:
                    main_class = obj()
                    MODULES.append(main_class)
        except ModuleNotFoundError:
            pass


def get_modules():
    ret = []
    for module in MODULES:
        ret.append({module.name: module.description})
    return ret


def get_module_by_index(index):
    try:
        return MODULES[index]
    except Exception as e:
        return None
