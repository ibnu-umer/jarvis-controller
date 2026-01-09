from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure





def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


class ScreenTimeWindow(QMainWindow):
    def __init__(self, screen_time_obj):
        super().__init__()
        self.screen_time_obj = screen_time_obj

        self.current_date = date.today()

        self.setWindowTitle("Screen Time Usage")
        self.resize(900, 600)

        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # ---------- HEADER ----------
        header = QHBoxLayout()

        self.prev_btn = QPushButton("◀")
        self.prev_btn.clicked.connect(self.prev_day)

        self.next_btn = QPushButton("▶")
        self.next_btn.clicked.connect(self.next_day)

        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        header.addWidget(self.prev_btn)
        header.addWidget(self.date_label, 1)
        header.addWidget(self.next_btn)

        main_layout.addLayout(header)

        # ---------- CONTENT ----------
        content = QHBoxLayout()
        content.setSpacing(12)

        # Donut chart
        self.figure = Figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.figure)
        content.addWidget(self.canvas, 2)

        # App list
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        title = QLabel("App Usage (Sorted)")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        right_layout.addWidget(title)

        self.list_widget = QListWidget()
        right_layout.addWidget(self.list_widget)

        content.addWidget(right_panel, 1)
        main_layout.addLayout(content)

        self.refresh()

    # ---------- DAY NAV ----------
    def prev_day(self):
        self.current_date -= timedelta(days=1)
        self.refresh()

    def next_day(self):
        if self.current_date < date.today():
            self.current_date += timedelta(days=1)
            self.refresh()

    # ---------- REFRESH ----------
    def refresh(self):
        self.date_label.setText(self.current_date.strftime("%d %b %Y"))

        data = self.screen_time_obj.get(self.current_date)
        self._populate(data)

    # ---------- UI UPDATE ----------
    def _populate(self, app_usage: dict[str, int]):
        self.figure.clear()
        self.list_widget.clear()

        if not app_usage:
            self.canvas.draw()
            return

        sorted_items = sorted(
            app_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )

        labels = [app for app, _ in sorted_items]
        values = [sec for _, sec in sorted_items]
        total_seconds = sum(values)

        ax = self.figure.add_subplot(111)
        ax.pie(
            values,
            startangle=90,
            wedgeprops=dict(width=0.35, edgecolor="white")
        )
        ax.set(aspect="equal")
        ax.set_title("Screen Usage Time")

        ax.text(
            0, 0,
            format_duration(total_seconds),
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold"
        )

        self.canvas.draw()

        for app, seconds in sorted_items:
            self.list_widget.addItem(
                QListWidgetItem(f"{app} — {format_duration(seconds)}")
            )



# import sys
# import random
# from datetime import date

# from PyQt6.QtWidgets import QApplication


# def mock_data_provider(day: date):
#     random.seed(day.toordinal())
#     return {
#         "VS Code": random.randint(3000, 9000),
#         "Chrome": random.randint(2000, 7000),
#         "Spotify": random.randint(500, 2000),
#         "Terminal": random.randint(800, 2500),
#         "Discord": random.randint(600, 1800),
#     }


# if __name__ == "__main__":
#     # app = QApplication(sys.argv)

#     # win = ScreenTimeWindow(mock_data_provider)
#     # win.show()

#     # sys.exit(app.exec())
#     from src.core.registry import MODULE_REGISTRY

#     print(MODULE_REGISTRY._instances.get("screentime_module"))
