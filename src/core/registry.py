import importlib, json
import pkgutil
from modules import __path__ as modules_path
from core.logger import logger
from core.base_module import BaseModule
from configs.config import FILE_REGISTRY_PATH
from pathlib import Path






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




class FileRegistry:
    def __init__(self, registry_file: str = FILE_REGISTRY_PATH):
        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.registry_file.exists():
            self.registry_file.write_text(json.dumps({}, indent=4), encoding="utf-8")

        self.entries = {} 
        self._load_registry()


    def _load_registry(self):
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self.entries = json.load(f)
                    logger.info("Registry loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading registry: {e}")
                self.entries = {}


    def _save_registry(self):
        try:
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving registry: {e}")


    def add_entry(self, name: str, path: str) -> bool:
        p = Path(path)
        if not p.exists():
            return False
        self.entries[name] = str(p.resolve())
        self._save_registry()
        return True
    

    def remove_entry(self, name: str) -> bool:
        if name in self.entries:
            self.entries.pop(name)
            self._save_registry()
            return True
        return False
    

    def get_path(self, name: str) -> str | None:
        return self.entries.get(name)
    

    def list_entries(self) -> dict:
        return self.entries.copy()
    

registry = FileRegistry()
