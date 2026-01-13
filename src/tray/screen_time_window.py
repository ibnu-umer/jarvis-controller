from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton
)
from PyQt6.QtGui import QFont, QColor, QBrush
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from configs.config import SCREEN_USAGE_WIN_HEIGHT, SCREEN_USAGE_WIN_WIDTH




class ScreenTimeWindow(QMainWindow):
    def __init__(self, screen_time_obj):
        super().__init__()
        self.screen_time_obj = screen_time_obj

        self.current_date = date.today()

        self.setWindowTitle("Screen Time Usage")
        self.resize(SCREEN_USAGE_WIN_HEIGHT, SCREEN_USAGE_WIN_WIDTH)
        self._build_ui()

    def _build_ui(self):
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
        self.figure = Figure(figsize=(5, 5), facecolor="#1e1e1e")
        self.canvas = FigureCanvas(self.figure)
        content.addWidget(self.canvas, 2)

        # App list
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        title = QLabel("App Usage")
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
        
        usage_cleaned = {app:sec for app, sec in app_usage.items() if sec > 120}
        sorted_items = sorted(
            usage_cleaned.items(),
            key=lambda x: x[1],
            reverse=True
        )

        labels = [app for app, _ in sorted_items]
        values = [sec for _, sec in sorted_items]
        total_seconds = sum(values)

        ax = self.figure.add_subplot(111)
        wedges, _ = ax.pie(
            values,
            startangle=90,
            wedgeprops=dict(width=0.35, edgecolor="white")
        )
        ax.set(aspect="equal")
        ax.set_title("Screen Usage Time")

        ax.text(
            0, 0,
            self.format_duration(total_seconds),
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            color="white"
        )

        self.canvas.draw()

        for (app, seconds), wedge in zip(sorted_items, wedges):
            r, g, b, _ = wedge.get_facecolor()
            color = QColor(
                int(r * 255),
                int(g * 255),
                int(b * 255)
            )
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color.name()};")

            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(8, 2, 8, 2)

            app_label = QLabel(app)
            app_label.setStyleSheet("color: white;")

            time_label = QLabel(self.format_duration(seconds))
            time_label.setStyleSheet("color: white;")
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

            layout.insertWidget(0, dot)
            layout.addWidget(app_label)
            layout.addStretch()
            layout.addWidget(time_label)

            item = QListWidgetItem()
            item.setSizeHint(container.sizeHint())

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, container)

    
    # ---------- HELPERS -------------

    def format_duration(seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"