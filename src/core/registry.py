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



class FileRegistry:
    def __init__(self, registry_file: str = FILE_REGISTRY_PATH):
        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.registry_file.exists():
            self.registry_file.write_text(json.dumps({}, indent=4), encoding="utf-8")

        self._entries = {} 
        self.load_file_registries()

    def load_file_registries(self):
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self._entries = json.load(f)
                    logger.info("File Registry loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading registry: {e}")
                self._entries = {}
    
    

    def get_path(self, app_name: str):
        return self._entries.get(app_name)
    

    def get_files(self):
        return self._entries
    

    def match_key(self, text):
        for name, path in self._entries.items():
            if name in text:
                return name, path
        return
    


class ModuleRegistry:
    def __init__(self):
        self._instances = {}
        self.load_all_modules()

    def register(self, cls):
        try:
            instance = cls()
            self._instances[cls.__name__] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to instantiate {cls.__name__}: {e}")
            return None

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

        logger.info(f"Modules loaded: {list(self._instances.keys())}")   
    
    def get_module(self, module_name):
        return self._instances.get(module_name)
    
    def get_modules(self):
        return self._instances
        
    


file_registry = FileRegistry()
module_registry = ModuleRegistry()
