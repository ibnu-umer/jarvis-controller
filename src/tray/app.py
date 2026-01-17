import sys, time, webbrowser, requests, asyncio
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal

from configs.config import ICON_PATH
from core.logger import logger
from tray.popup import Popup 
from tray.screen_time_window import ScreenTimeWindow
from tray.template_window import TemplateEditorWindow
import keyboard, threading, httpx




class HotkeyBridge(QObject):
    toggle_requested = pyqtSignal()


class JarvisTray:

    def __init__(self, pipeline_runner, screen_time_obj, reminder_obj):
        self.pipeline_runner = pipeline_runner
        self.screen_time_obj = screen_time_obj
        self.reminder_obj = reminder_obj

        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon(str(ICON_PATH)))
        self.app.setQuitOnLastWindowClosed(False)

        self.screen_time_window = ScreenTimeWindow(screen_time_obj)
        self.template_window = TemplateEditorWindow()

        self.popup = Popup(
            self.app, self, self.screen_time_window, 
            self.template_window, self._run_command
        )
        self.popup.hide()

        # Tray icon
        self.tray_icon = QSystemTrayIcon(QIcon(str(ICON_PATH)), self.app)
        self.tray_icon.setToolTip("Jarvis")

        # Tray menu
        self.menu = QMenu()
        self._build_menu()
        self.tray_icon.setContextMenu(self.menu)

        self.tray_icon.show()

        self.hotkey_bridge = HotkeyBridge()
        self.hotkey_bridge.toggle_requested.connect(self.popup.toggle)

        threading.Thread(
            target=self.register_shortcut,
            daemon=True
        ).start()

        self.loop = asyncio.new_event_loop()
        threading.Thread(
            target=self._start_async_loop,
            daemon=True
        ).start()

        self.reminder_obj.set_trigger(self.reminder_trigger)

        logger.info("Jarvis Tray started")


    def _start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _run_command(self, user_input: str):
        return await self.pipeline_runner._run(user_input)

    def register_shortcut(self):
        """Global shortcut to toggle popup window."""
        keyboard.add_hotkey(
            'win+shift+j',
            lambda: self.hotkey_bridge.toggle_requested.emit()
        )
        keyboard.wait()


    # --------- Menu ---------

    def _build_menu(self):
        self.menu.clear()

        open_popup_action = QAction("Open Jarvis", self.menu)
        open_popup_action.triggered.connect(self.toggle_popup)

        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(self.quit_app)

        self.menu.addAction(open_popup_action)
        self.menu.addSeparator()
        self.menu.addAction(quit_action)


    # --------- Actions ---------

    def toggle_popup(self):
        if self.popup.isVisible():
            self.popup.hide()
        else:
            self.popup.show()
            self.popup.activateWindow()
            self.popup.raise_()

    @staticmethod
    def confirm_with_popup(message, title="Confirm"):
        reply = QMessageBox.question(
            None,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def quit_app(self):
        if not self.confirm_with_popup("Are you sure you want to quit Jarvis?"):
            return

        self.screen_time_obj.shutdown()
        self.reminder_obj.shutdown()
        self.popup.close()
        self.tray_icon.hide()
        self.app.quit()
        logger.info("Jarvis Tray stopped")

    def run(self):
        sys.exit(self.app.exec())


    def reminder_trigger(self, result):
        message = result["message"]
        logger.info(f"REMINDER: {message}")
        asyncio.run_coroutine_threadsafe(
            self.popup.tts.say(message),
            self.loop
        )
