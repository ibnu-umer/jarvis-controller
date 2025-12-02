from src.tray.tray_app import JarvisTray
from src.api.listener import WindowsListener
from src.core.registry import load_all_modules




def main():
    load_all_modules()  # load all module intances in registry

    windows_listener = WindowsListener()
    windows_listener.start()

    tray = JarvisTray()
    tray.run()



if __name__ == "__main__":
    main()
