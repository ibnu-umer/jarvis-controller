import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsEllipseItem,
    QGraphicsPathItem, QGraphicsProxyWidget
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QBrush, QColor, QPainterPath




# ---------------- BLOCK ITEM ---------------- #

class ActionNodeItem(QGraphicsRectItem):
    WIDTH = 240
    HEIGHT = 100

    def __init__(self, title: str, y: int, editor):
        super().__init__(0, 0, self.WIDTH, self.HEIGHT)
        self.setPos(0, y)   
        self.editor = editor

        self.setBrush(QBrush(QColor("#2b2b2b")))
        self.setPen(QColor("#555555"))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)

        # Title
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setPlainText(title)
        self.title_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.title_item.setTextWidth(self.WIDTH - 60)
        self.title_item.setPos(12, 8)

        # Result
        self.result_item = QGraphicsTextItem(self)
        self.result_item.setPlainText("Result: —")
        self.result_item.setDefaultTextColor(Qt.GlobalColor.gray)
        self.result_item.setTextWidth(self.WIDTH - 24)
        self.result_item.setPos(12, 42)

        # Input port (top center)
        self.input_port = QGraphicsEllipseItem(
            self.WIDTH / 2 - 6, -6, 12, 12, self
        )
        self.input_port.setBrush(QBrush(QColor("#4ade80")))

        # Output port (bottom center)
        self.output_port = QGraphicsEllipseItem(
            self.WIDTH / 2 - 6, self.HEIGHT - 6, 12, 12, self
        )
        self.output_port.setBrush(QBrush(QColor("#60a5fa")))

        # ---- CONTROL BUTTONS (Up / Delete / Down) ----
        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(2)

        btn_up = QPushButton("↑")
        btn_up.setFixedSize(22, 22)
        btn_up.clicked.connect(self.move_up)

        btn_delete = QPushButton("✕")
        btn_delete.setFixedSize(22, 22)
        btn_delete.clicked.connect(self.delete_self)

        btn_down = QPushButton("↓")
        btn_down.setFixedSize(22, 22)
        btn_down.clicked.connect(self.move_down)

        controls_layout.addWidget(btn_up)
        controls_layout.addWidget(btn_delete)
        controls_layout.addWidget(btn_down)

        proxy = QGraphicsProxyWidget()
        proxy.setWidget(controls)
        proxy.setParentItem(self)
        proxy.setPos(self.WIDTH - 30, 8)


    def move_up(self):
        self.editor.move_block(self, direction=-1)


    def move_down(self):
        self.editor.move_block(self, direction=1)


    def set_result(self, text: str):
        self.result_item.setPlainText(f"Result: {text}")


    def delete_self(self):
        self.editor.remove_block(self)



# ---------------- CONNECTION ---------------- #

class ConnectionItem(QGraphicsPathItem):
    def __init__(self, start_item, end_item):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.setPen(QColor("#9ca3af"))
        self.update_path()

    def update_path(self):
        start_port = self.start_item.output_port
        end_port = self.end_item.input_port

        start = start_port.mapToScene(start_port.boundingRect().center())
        end = end_port.mapToScene(end_port.boundingRect().center())

        path = QPainterPath(start)

        dy = abs(end.y() - start.y())
        ctrl1 = QPointF(start.x(), start.y() + dy * 0.5)
        ctrl2 = QPointF(end.x(), end.y() - dy * 0.5)

        path.cubicTo(ctrl1, ctrl2, end)
        self.setPath(path)


# ---------------- MAIN WINDOW ---------------- #

class TemplateEditorWindow(QMainWindow):
    BLOCK_SPACING = 140

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jarvis Template Editor")
        self.resize(820, 460)

        self.blocks = []
        self.connections = []

        self._init_ui()


    def _init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)

        # ---------- ACTION SIDEBAR ---------- #
        self.sidebar = QListWidget()
        self.sidebar.addItems([
            "get_folder_name",
            "open_folder",
            "read_file",
            "send_notification"
        ])
        self.sidebar.setFixedWidth(160)
        layout.addWidget(self.sidebar)

        # ---------- CANVAS ---------- #
        self.scene = QGraphicsScene()
        self.scene.selectionChanged.connect(self.on_selection_changed)

        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        layout.addWidget(self.view, 1)

        # ---------- TEST PANEL ---------- #
        test_main_layout = QVBoxLayout()
        test_widget = QWidget()
        test_widget.setFixedWidth(220)
        test_layout = QVBoxLayout()

        self.test_label = QLabel("No action selected")
        self.test_result = QLabel("—")

        self.test_btn = QPushButton("Test Action")
        self.test_btn.clicked.connect(self.test_selected)

        test_layout.addWidget(QLabel("Action Test"))
        test_layout.addWidget(self.test_label)
        test_layout.addWidget(self.test_result)
        test_layout.addStretch()      
        test_layout.addWidget(self.test_btn)

        test_widget.setLayout(test_layout)
        test_main_layout.addWidget(test_widget)
        layout.addLayout(test_main_layout)

        # ---------- SIGNALS ---------- #
        self.sidebar.itemDoubleClicked.connect(self.add_block)
        self.scene.selectionChanged.connect(self.on_selection_changed)


    # ---------- LOGIC ---------- #

    def add_block(self, item):
        y = len(self.blocks) * 140
        block = ActionNodeItem(item.text(), y, self)
        self.scene.addItem(block)
        self.blocks.append(block)

        if len(self.blocks) > 1:
            conn = ConnectionItem(self.blocks[-2], block)
            self.scene.addItem(conn)
            self.connections.append(conn)

        self.scene.setSceneRect(self.scene.itemsBoundingRect())
 

    def remove_block(self, block):
        self.scene.removeItem(block)
        self.blocks.remove(block)

        self.scene.blockSignals(True)
        self.relayout_blocks()
        self.scene.blockSignals(False)

        for conn in self.connections:
            conn.update_path()


    def on_selection_changed(self):
        if not self.scene:
            return

        try:
            items = self.scene.selectedItems()
        except RuntimeError:
            return

        if items:
            block = items[0]
            self.test_label.setText(block.title_item.toPlainText())
        else:
            self.test_label.setText("No action selected")


    def test_selected(self):
        items = self.scene.selectedItems()
        if not items:
            self.test_result.setText("Nothing selected")
            return

        block = items[0]
        # fake test result
        result = "OK"
        block.set_result(result)
        self.test_result.setText(result)


    def relayout_blocks(self):
        # Reposition blocks
        for i, block in enumerate(self.blocks):
            block.setPos(0, i * self.BLOCK_SPACING)

        # Rebuild connections
        for conn in self.connections:
            self.scene.removeItem(conn)
        self.connections.clear()

        for i in range(len(self.blocks) - 1):
            conn = ConnectionItem(self.blocks[i], self.blocks[i + 1])
            self.scene.addItem(conn)
            self.connections.append(conn)

        self.scene.setSceneRect(self.scene.itemsBoundingRect())


    def move_block(self, block, direction: int):
        idx = self.blocks.index(block)
        new_idx = idx + direction

        if new_idx < 0 or new_idx >= len(self.blocks):
            return  # out of bounds

        # Swap
        self.blocks[idx], self.blocks[new_idx] = (
            self.blocks[new_idx],
            self.blocks[idx],
        )

        self.scene.blockSignals(True)
        self.relayout_blocks()
        self.scene.blockSignals(False)


    def closeEvent(self, event):
        try:
            self.scene.selectionChanged.disconnect(self.on_selection_changed)
        except Exception:
            pass
        super().closeEvent(event)




# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TemplateEditorWindow()
    win.show()
    sys.exit(app.exec())
