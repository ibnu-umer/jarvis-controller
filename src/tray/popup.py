import sys, time, threading, requests

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

WINDOW_WIDTH = 480
WINDOW_HEIGHT = 360

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
    def __init__(self, app):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        screen_geom = app.primaryScreen().geometry()
        x = screen_geom.width() - self.width() - 20  
        y = screen_geom.height() - self.height() - 40 
        self.move(x, y)

        self._build_ui()
        ui_state.updated.connect(self._on_state_update)

        # StatusStreamThread().start()

    # ---------- UI ----------

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a command…")
        self.input.returnPressed.connect(self._send_command)

        self.response = QLabel("")
        self.response.setWordWrap(True)

        self.task_list = QListWidget()

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._send_command)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input)
        input_row.addWidget(send_btn)

        layout.addLayout(input_row)
        layout.addWidget(self.response)
        layout.addWidget(self.task_list)

    # ---------- EVENTS ----------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    # ---------- NETWORK ----------

    def _send_command(self):
        text = self.input.text().strip()
        if not text:
            return

        self.input.clear()

        try:
            requests.post(
                WSL_BASE_URL + COMMAND_ENDPOINT,
                json={"text": text},
                timeout=2,
            )
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
            bar.setRange(0, 0)  # indeterminate
        else:
            bar.setRange(0, 100)
            bar.setValue(int(task["progress"] * 100))

        layout.addWidget(label)
        layout.addWidget(bar)
        return container


# ---------- STANDALONE RUN ----------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    popup = Popup()
    popup.show()
    sys.exit(app.exec())
