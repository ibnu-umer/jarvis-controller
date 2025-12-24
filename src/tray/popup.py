import sys, time, threading, requests, asyncio

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
from configs.config import WSL_BASE_URL


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

    def run(self):
        url = f"{WSL_BASE_URL}/status/stream"
        self._stop_event = threading.Event()

        while not self._stop_event.is_set():
            try:
                with requests.get(url, stream=True, timeout=5) as r:
                    for line in r.iter_lines():
                        if self._stop_event.is_set():
                            return
                        if line:
                            self.handle_event(line)
            except requests.RequestException:
                time.sleep(2)


class Popup(QWidget):
    def __init__(self, app, parent):
        super().__init__()
        self._parent = parent

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

        # StatusStreamThread().start()

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
        self.response.setWordWrap(True)

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
        layout.addWidget(self.response)
        layout.addWidget(self.task_list)



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
            await self._parent.backend_command_trigger(text)
        except Exception as e:
            print(e)
            self.response.setText("Backend not reachable")

    # ---------- STATE UPDATE ----------

    def _on_state_update(self, state: dict):
        self.response.setText(state.get("response", {}).get("text", ""))

        self.task_list.clear()

        for task in state.get("tasks", []):
            item = QListWidgetItem()
            widget = self._task_widget(task)
            item.setSizeHint(widget.sizeHint())
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, widget)

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

