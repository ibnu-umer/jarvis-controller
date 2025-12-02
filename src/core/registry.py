import importlib, os
from src.core.base_module import BaseModule
import pkgutil
from src import modules





FUNCTION_REGISTRY = {}

def action(name=None, params=None):
    def wrapper(func):
        module = func.__module__
        qual = func.__qualname__.split(".")
        cls_name = qual[-2] if len(qual) > 1 else None

        FUNCTION_REGISTRY[name or func.__name__] = {
            "module": module,
            "class": cls_name,
            "function": func.__name__,
            "params": params or [],
        }
        return func
    return wrapper



MODULE_INSTANCES = {}

def load_all_modules():
    for _, module_name, _ in pkgutil.iter_modules(modules.__path__):
        full_path = f"src.modules.{module_name}"
        try:
            importlib.import_module(full_path)
        except Exception as e:
            print(f"❌ Failed to import {full_path}: {e}")

    for cls in BaseModule.__subclasses__():
        try:
            MODULE_INSTANCES[cls.__name__] = cls()
        except Exception as e:
            print(f"❌ Failed to instantiate {cls.__name__}: {e}")


        

