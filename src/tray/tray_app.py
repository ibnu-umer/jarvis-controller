import sys, time, webbrowser, requests
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal

from configs.config import WIN_BASE_URL, WSL_BASE_URL
from core.logger import logger
from tray.popup import Popup 
import keyboard, threading, httpx, asyncio




class HotkeyBridge(QObject):
    toggle_requested = pyqtSignal()


class JarvisTray:
    PING_INTERVAL = 6000  # milliseconds
    ICON_SIZE = 64
    TEXT_ICON_CHAR = "J"

    def __init__(self, backend_base=WSL_BASE_URL, ui_url=WIN_BASE_URL, shutdown_func=None):
        self.backend_base = backend_base.rstrip("/")
        self.ui_url = ui_url
        self.shutdown_func = shutdown_func

        self.healthy = False
        self.last_checked = None

        self.app = QApplication(sys.argv)
        self.popup = Popup(self.app, self)
        self.popup.hide()

        # Tray icon
        self.tray_icon = QSystemTrayIcon(QIcon(self.make_icon()), self.app)
        self.tray_icon.setToolTip("Jarvis Assistant")

        # Tray menu
        self.menu = QMenu()
        self._build_menu()
        self.tray_icon.setContextMenu(self.menu)

        # Timer for backend ping
        self.timer = QTimer()
        self.timer.timeout.connect(self.health_check)
        self.timer.start(self.PING_INTERVAL)

        self.tray_icon.show()

        self.hotkey_bridge = HotkeyBridge()
        self.hotkey_bridge.toggle_requested.connect(self.popup.toggle)

        threading.Thread(
            target=self.register_shortcut,
            daemon=True
        ).start()

        logger.info("Jarvis Tray started")
        


    # --------- Icon ---------
    def make_icon(self):
        pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        color = QColor(88, 214, 141) if self.healthy else QColor(239, 68, 68)
        painter.setBrush(color)
        painter.setPen(Qt.GlobalColor.transparent)
        painter.drawEllipse(0, 0, self.ICON_SIZE, self.ICON_SIZE)

        font = QFont("Segoe UI", 28)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, self.TEXT_ICON_CHAR)
        painter.end()

        return QIcon(pixmap)
    

    def register_shortcut(self):
        """Global shortcut to toggle popup window."""
        keyboard.add_hotkey(
            'win+shift+j',
            lambda: self.hotkey_bridge.toggle_requested.emit()
        )
        keyboard.wait()
    

    # --------- Backend ---------
    def backend_ping(self):
        url = f"{self.backend_base}/health"
        try:
            r = requests.get(url, timeout=2)
            return r.status_code == 200
        except requests.RequestException:
            return False
        

    def health_check(self):
        self.healthy = self.backend_ping()
        self.last_checked = time.strftime("%Y-%m-%d %H:%M:%S")
        self.tray_icon.setIcon(self.make_icon())
        self._build_menu()


    async def backend_command_trigger(self, text):
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(
                f"{self.backend_base}/command",
                json={"user_input": text}
            )
            r.raise_for_status()
            return r.json()


    # --------- Menu ---------
    def _build_menu(self):
        self.menu.clear()

        status_action = QAction(f"Backend: {'OK' if self.healthy else 'DOWN'}")
        status_action.setEnabled(False)
        last_action = QAction(f"Last: {self.last_checked if self.last_checked else 'never'}")
        last_action.setEnabled(False)

        open_ui_action = QAction("Open UI", self.menu)
        open_ui_action.triggered.connect(self.open_ui)

        refresh_action = QAction("Ping backend", self.menu)
        refresh_action.triggered.connect(self.health_check)

        reload_data_action = QAction("Refresh Data", self.menu)
        reload_data_action.triggered.connect(lambda: self.call_action("refresh"))

        open_popup_action = QAction("Open Jarvis Popup", self.menu)
        open_popup_action.triggered.connect(self.toggle_popup)

        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(self.quit_app)

        self.menu.addAction(status_action)
        self.menu.addAction(last_action)
        self.menu.addSeparator()
        self.menu.addAction(open_ui_action)
        self.menu.addAction(refresh_action)
        self.menu.addAction(reload_data_action)
        self.menu.addAction(open_popup_action)
        self.menu.addSeparator()
        self.menu.addAction(quit_action)


    # --------- Actions ---------
    def open_ui(self):
        webbrowser.open(self.ui_url)


    def call_action(self, action_name):
        url = f"{self.backend_base}/action/{action_name}"
        try:
            r = requests.post(url, timeout=3)
            if r.status_code == 200:
                logger.info(f"Action {action_name} OK: {r.text}")
            else:
                logger.warning(f"Action {action_name} returned {r.status_code}: {r.text}")
        except Exception as e:
            logger.error(f"Action call failed: {e}")
        self.health_check()


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
        if self.confirm_with_popup("Are you sure you want to quit Jarvis?"):
            self.shutdown_func()
            self.popup.close()
            self.tray_icon.hide()
            self.app.quit()

            logger.info("Jarvis Tray stopped")


    def run(self):
        sys.exit(self.app.exec())
