import threading, sys, os, asyncio
from qasync import QEventLoop


# Add src folder to sys.path
SRC_PATH = os.path.join(os.path.dirname(__file__), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

try:
    from tray.tray_app import JarvisTray
    from api.listener import WindowsListener
    from core.registry import load_registry, MODULE_REGISTRY
    from core.logger import logger
except Exception as e:
    print(e)






def run_tray(windows_listener, shutdown_func):
    tray = JarvisTray(shutdown_func=shutdown_func)
    loop = QEventLoop(tray.app)
    asyncio.set_event_loop(loop)

    windows_listener.tray = tray

    with loop:
        loop.run_forever()









if __name__ == "__main__":
    try:
        load_registry()
        screen_time_obj = MODULE_REGISTRY._instances.get("ScreenTimeModule")

        windows_listener = WindowsListener()
        listener_thread = threading.Thread(target=windows_listener.start, daemon=True)
        listener_thread.start()

        def shutdown():
            windows_listener.stop()
            screen_time_obj.shutdown()

        run_tray(windows_listener, shutdown)

    except Exception as e:
        logger.error(f"Error while running script: {e}")
