import importlib
import pkgutil
from modules import __path__ as modules_path
from core.logger import logger
from core.base_module import BaseModule






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



class ModuleRegistry:
    def __init__(self):
        self._instances = {}

    def register(self, cls):
        try:
            instance = cls()
            self._instances[cls.__name__] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to instantiate {cls.__name__}: {e}")
            return None

    def get(self, cls_name):
        return self._instances.get(cls_name)

    def load_all_modules(self):
        # Dynamically import all modules inside src/modules
        logger.debug(f"Modules Path: {modules_path}")
        for _, module_name, _ in pkgutil.iter_modules(modules_path):
            full_path = f"modules.{module_name}" 
            try:
                importlib.import_module(full_path)
            except Exception as e:
                logger.error(f"Failed to import {full_path}: {e}")

        # Explicitly register subclasses
        for cls in BaseModule.__subclasses__():
            self.register(cls)



MODULE_REGISTRY = ModuleRegistry()

def load_registry():
    MODULE_REGISTRY.load_all_modules()   
    logger.info(f"Modules loaded: {list(MODULE_REGISTRY._instances.keys())}")     

