import threading, sys, os, asyncio, traceback
from qasync import QEventLoop


# Add src folder to sys.path
SRC_PATH = os.path.join(os.path.dirname(__file__), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

try:
    from tray.app import JarvisTray
    from core.logger import logger
    from core.pipeline import PipeLineRunner
    from core.registry import module_registry
except Exception as e:
    traceback.print_exc()
    print(f"Error in tray: {e}")


def main():
    try:
        pipeline_runner = PipeLineRunner()
        screen_time_obj = module_registry.get_module("ScreenTimeModule")
        reminder_obj = module_registry.get_module("Reminder")

        tray = JarvisTray(pipeline_runner, screen_time_obj, reminder_obj)
        loop = QEventLoop(tray.app)
        asyncio.set_event_loop(loop)

        with loop:
            loop.run_forever()

    except Exception as e:
        logger.error(f"Error while running script: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
