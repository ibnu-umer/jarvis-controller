import sys, time, threading, requests, asyncio, json

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt
from configs.config import WSL_BASE_URL, SCREENTIME_DATA

from tray.screen_time_window import ScreenTimeWindow
from core.logger import logger


# ================= CONFIG =================

STATUS_STREAM_ENDPOINT = "/status/stream"
COMMAND_ENDPOINT = "/command"

WINDOW_WIDTH = 320
WINDOW_HEIGHT = 260

# =========================================


class UIState(QObject):
    updated = pyqtSignal(dict)

    def update(self, payload: dict):
        self.updated.emit(payload)


ui_state = UIState()


class StatusStreamThread(threading.Thread):
    daemon = True

    def __init__(self, command_id: str):
        super().__init__()
        self.command_id = command_id
        self._stop_event = threading.Event()


    def stop(self):
        self._stop_event.set()


    def run(self):
        url = f"{WSL_BASE_URL}/status/stream/{self.command_id}"

        while not self._stop_event.is_set():
            try:
                with requests.get(url, stream=True, timeout=(5, None)) as r:
                    r.raise_for_status()

                    for line in r.iter_lines():
                        if self._stop_event.is_set():
                            return

                        if not line:
                            continue

                        self.handle_event(line)

                return

            except requests.RequestException:
                if self._stop_event.is_set():
                    return
                time.sleep(5)  


    def handle_event(self, raw_line: bytes):
        try:
            payload = json.loads(raw_line.decode())
            ui_state.update(payload)
        except Exception:
            pass



class Popup(QWidget):
    def __init__(self, app, parent, screen_time_obj=None):
        super().__init__()
        self._parent = parent
        self.screen_time_obj = screen_time_obj

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._build_ui()
        self._set_style()

        self.adjustSize()
        self._move_to_corner(app)
        ui_state.updated.connect(self._on_state_update)


    # ---------- UI ----------

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget(self)
        self.container.setObjectName("main")
        outer.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a command…")
        self.input.returnPressed.connect(self._send_command)

        self.response = QLabel("")
        response_font = QFont()
        response_font.setPointSize(6)
        self.response.setFont(response_font)
        self.response.setWordWrap(True)

        screen_usage_btn = QPushButton("U")
        screen_usage_btn.setFixedWidth(30)
        screen_usage_btn.clicked.connect(self._show_screen_usage)

        info_row = QHBoxLayout()
        info_row.addWidget(self.response)
        info_row.addWidget(screen_usage_btn)

        self.task_list = QListWidget()

        send_btn = QPushButton(">")
        send_btn.setFixedWidth(30)
        send_btn.clicked.connect(self._send_command)

        close_btn = QPushButton("X")
        close_btn.setFixedWidth(30)
        close_btn.clicked.connect(self.toggle)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input)
        input_row.addWidget(send_btn)
        input_row.addWidget(close_btn)

        layout.addLayout(input_row)
        layout.addLayout(info_row)
        layout.addWidget(self.task_list)


    def create_task_item(self, item: QListWidgetItem, user_input: str, actions: list[str], success: bool, message: str=""):
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(4)

        # ---------- HEADER ----------

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        user_label = QLabel(user_input)
        user_label.setWordWrap(True)
        user_label.setCursor(Qt.CursorShape.PointingHandCursor)

        user_font = QFont()
        user_font.setPointSize(7)
        user_font.setBold(True)
        user_label.setFont(user_font)

        status_dot = QLabel("●")
        status_dot.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        status_dot.setStyleSheet(
            f"color: {'#22c55e' if success else '#ef4444'};"
        )

        header_layout.addWidget(user_label, 1)
        header_layout.addWidget(status_dot)

        # ---------- ACTIONS ----------

        actions_container = QWidget()
        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setContentsMargins(12, 2, 0, 0)
        actions_layout.setSpacing(2)

        action_font = QFont()
        action_font.setPointSize(6)

        for action in actions:
            label = QLabel(f"- {action}")
            label.setFont(action_font)
            label.setStyleSheet("color: #9ca19e;")
            actions_layout.addWidget(label)

        message_label = QLabel(message)
        color = "#96e0a7" if success else "#e09698"
        message_label.setStyleSheet(f"color: {color};")
        message_font = QFont()
        message_font.setPointSize(6)
        message_label.setFont(message_font)
        actions_layout.addWidget(message_label)

        actions_container.setVisible(False)

        # ---------- TOGGLE ----------

        def toggle_actions():
            actions_container.setVisible(not actions_container.isVisible())
            container.adjustSize()
            item.setSizeHint(container.sizeHint())

        user_label.mousePressEvent = lambda _: toggle_actions()

        # ---------- ASSEMBLE ----------

        main_layout.addWidget(header)
        main_layout.addWidget(actions_container)

        return container


    def _set_style(self):
        self.setStyleSheet("""
            QWidget#main {
                background-color: #0f172a;
                border: 2px solid #53658f;
                border-radius: 10px;
                color: #e5e7eb;
            }
            QLineEdit {
                background-color: #020617;
                border: 1px solid #53658f;
                border-radius: 6px;
                padding: 6px;
                color: #e5e7eb;
            }
        """)


    def _move_to_corner(self, app):
        screen = app.primaryScreen().availableGeometry()
        self.move(
            screen.right() - self.width() - 20,
            screen.bottom() - self.height() - 40
        )


    # ---------- EVENTS ----------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()


    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()


    # ---------- NETWORK ----------

    def _send_command(self):
        text = self.input.text().strip()
        if not text:
            return

        self.input.clear()
        asyncio.create_task(self._send_command_async(text))


    async def _send_command_async(self, text):
        try:
            resp = await self._parent.backend_command_trigger(text)
            self.stream_thread = StatusStreamThread(resp["command_id"])
            self.stream_thread.start()
        except Exception as e:
            logger.warning(f"Backend not reachable: {e}")
            self.response.setText("Backend not reachable")

    # ---------- STATE UPDATE ----------

    def _on_state_update(self, state: dict):
        user_input = state.get("user_input", "")
        actions = state.get("executed_actions", [])
        success = True if "done" in actions else False
        message = state.get("message", "")

        item = QListWidgetItem(self.task_list)
        widget = self.create_task_item(
            item=item,
            user_input=user_input,
            actions=actions,
            success=success,
            message=message
        )

        item.setSizeHint(widget.sizeHint())
        self.task_list.setItemWidget(item, widget)
        self.task_list.scrollToBottom()



    def _task_widget(self, task: dict):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        label = QLabel(f"{task['label']} — {task['status']}")
        bar = QProgressBar()

        if task.get("progress") is None:
            bar.setRange(0, 0)  
        else:
            bar.setRange(0, 100)
            bar.setValue(int(task["progress"] * 100))

        layout.addWidget(label)
        layout.addWidget(bar)
        return container


    def _show_screen_usage(self):
        self.screen_time_window = ScreenTimeWindow(self.screen_time_obj)
        self.screen_time_window.show()

 

