import os
import importlib
import inspect

from base_module import BaseModule


MODULES_DIR_NAME = "modules"


MODULES = {}


def load():

    current_dir = os.path.dirname(os.path.abspath(__file__))

    modules_path = f"{current_dir}/{MODULES_DIR_NAME}"
    dirs = os.listdir(modules_path)

    module_dirs = []

    for dir in dirs:
        if os.path.isdir(f"{current_dir}/{MODULES_DIR_NAME}/{dir}"):
            module_dirs.append(dir)

    for module_dir in module_dirs:
        try:

            module = importlib.import_module(f"{MODULES_DIR_NAME}.{module_dir}.main")

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseModule) and obj is not BaseModule:

                    main_class = obj()
                    MODULES[len(MODULES)+1] = main_class

        except ModuleNotFoundError:
            pass


def get_modules():
    return MODULES


def get_modules_string():
    ret = ""
    for module_num in MODULES:
        ret += f"{module_num}. '{MODULES[module_num].name}' - {MODULES[module_num].description}\n"
    return ret


def get_module_by_index(index):
    try:
        return MODULES[index]
    except Exception as e:
        return None
