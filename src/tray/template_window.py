import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsEllipseItem, 
    QGraphicsPathItem, QGraphicsProxyWidget, QLineEdit
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QBrush, QColor, QPainterPath, QFont

from core.registry import FUNCTION_REGISTRY, module_registry
from core.logger import logger

from uuid import uuid4


# ---------------- BLOCK ITEM ---------------- #

class ActionNodeItem(QGraphicsRectItem):
    WIDTH = 240
    HEIGHT = 100

    def __init__(self, action: str, y: int, editor, block_id):
        super().__init__(0, 0, self.WIDTH, self.HEIGHT)
        self.setPos(0, y)   
        self.editor = editor
        self.block_id = block_id
        params = FUNCTION_REGISTRY[action].get("params")
        self.params = {p: None for p in params}

        self.setBrush(QBrush(QColor("#2b2b2b")))
        self.setPen(QColor("#555555"))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)

        # Title
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setPlainText(action)
        self.title_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.title_item.setTextWidth(self.WIDTH - 60)
        self.title_item.setPos(12, 8)

        # Result
        self.result_item = QGraphicsTextItem(self)
        self.result_item.setPlainText("Result: —")
        self.result_item.setDefaultTextColor(Qt.GlobalColor.gray)
        self.result_item.setTextWidth(self.WIDTH - 24)
        self.result_item.setPos(12, 68)

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
        self.editor.remove_block(self.block_id)



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

        self.blocks = {}
        self.connections = []
        self.context = {}

        self._init_ui()
        self._populate_sidebar()


    def _init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)

        # ---------- ACTION SIDEBAR ---------- #
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(160)
        layout.addWidget(self.sidebar)

        # ---------- CANVAS ---------- #
        self.scene = QGraphicsScene()
        self.scene.selectionChanged.connect(self.on_selection_changed)

        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        layout.addWidget(self.view, 1)

        # ---------- TEST PANEL ---------- #
        test_widget = QWidget()
        test_widget.setFixedWidth(220)

        self.test_layout = QVBoxLayout(test_widget)
        self.test_layout.setContentsMargins(8, 8, 8, 8)

        self.test_title = QLabel("Action Test")
        self.test_label = QLabel("No action selected")
        self.test_desc = QLabel("")
        self.test_desc.setWordWrap(True)

        self.params_container = QVBoxLayout()   # dynamic inputs

        self.test_result = QLabel("")
        self.test_btn = QPushButton("Test Action")
        self.test_btn.clicked.connect(self.test_selected)

        self.test_layout.addWidget(self.test_title)
        self.test_layout.addWidget(self.test_label)
        self.test_layout.addWidget(self.test_desc)
        self.test_layout.addSpacing(8)
        self.test_layout.addLayout(self.params_container)

        self.test_layout.addStretch()
        self.test_layout.addWidget(self.test_result)
        self.test_layout.addWidget(self.test_btn)

        test_widget.setLayout(self.test_layout)
        layout.addWidget(test_widget)

        # ---------- SIGNALS ---------- #
        self.sidebar.itemDoubleClicked.connect(self.add_block)
        self.scene.selectionChanged.connect(self.on_selection_changed)


    # ---------- LOGIC ---------- #

    def add_block(self, item):
        y = len(self.blocks) * self.BLOCK_SPACING
        block_id = uuid4()
        block = ActionNodeItem(item.text(), y, self, block_id)
        self.scene.addItem(block)

        self.blocks[block_id] = block
        self.relayout_blocks()
 

    def remove_block(self, block_id):
        block = self.blocks.pop(block_id, None)
        if not block:
            return

        self.scene.removeItem(block)

        self.scene.blockSignals(True)
        self.relayout_blocks()
        self.scene.blockSignals(False)

        del self.context[block_id] # remove data from context

        for conn in self.connections:
            conn.update_path()


    def on_selection_changed(self):
        try:
            items = self.scene.selectedItems()
        except RuntimeError:
            return

        self.clear_params()

        if not items:
            self.test_label.setText("No action selected")
            self.test_desc.setText("")
            self.test_result.setText("")
            return

        block = items[0]
        action_name = block.title_item.toPlainText()
        self.test_label.setText(action_name)

        info = FUNCTION_REGISTRY.get(action_name)
        if not info:
            self.test_desc.setText("No metadata available")
            return

        # Description
        self.test_desc.setText(info.get("description", "No Description"))

        # Params
        tested_params = block.params
        self.param_inputs = {}  # store for testing
        for param in info.get("params", []):
            label = QLabel(param)
            input_box = QLineEdit()
            input_box.setPlaceholderText(param)

            self.params_container.addWidget(label)
            self.params_container.addWidget(input_box)

            self.param_inputs[param] = input_box
            
            if param in tested_params:
                input_box.setText(tested_params[param])



    def test_selected(self):
        items = self.scene.selectedItems()
        if not items:
            return

        block = items[0]
        block_id = block.block_id 

        action_name = block.title_item.toPlainText()
        params = {
            name: box.text()
            for name, box in self.param_inputs.items()
            if box.text() != ""
        }
        block.params.update(params)
        logger.info(f"[TEST] action: {action_name} | params: {params}")

        result = self.run_action(action_name, params)
        logger.info(f"[TEST] result: {result}")

        self.context[block_id] = result["data"]
        self.test_result.setText("Success" if result["success"] else "Failure")
        logger.info(f"[TEST] context: {list(self.context.values())}")


    def run_action(self, action, params):
        func_info = FUNCTION_REGISTRY.get(action)
        instance = module_registry.get_module(func_info["class"])
        action_func = getattr(instance, func_info["function"], None)
        return action_func(**params)


    def clear_params(self):
        while self.params_container.count():
            item = self.params_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


    def relayout_blocks(self):
        blocks = list(self.blocks.values())

        for i, block in enumerate(blocks):
            block.setPos(0, i * self.BLOCK_SPACING)

        # Remove old connections
        for conn in self.connections:
            self.scene.removeItem(conn)
        self.connections.clear()

        # Rebuild connections in visual order
        for i in range(len(blocks) - 1):
            conn = ConnectionItem(blocks[i], blocks[i + 1])
            self.scene.addItem(conn)
            self.connections.append(conn)

        self.scene.setSceneRect(self.scene.itemsBoundingRect())


    def move_block(self, block, direction: int):
        items = list(self.blocks.items())

        idx = next(
            (i for i, (_, b) in enumerate(items) if b is block),
            None
        )
        if idx is None:
            return

        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(items):
            return

        items[idx], items[new_idx] = items[new_idx], items[idx]

        self.blocks = dict(items)

        self.scene.blockSignals(True)
        self.relayout_blocks()
        self.scene.blockSignals(False)


    def closeEvent(self, event):
        try:
            self.scene.selectionChanged.disconnect(self.on_selection_changed)
        except Exception:
            pass
        super().closeEvent(event)


    def _populate_sidebar(self):
        func_names = list(FUNCTION_REGISTRY.keys())
        self.sidebar.addItems(func_names)




# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TemplateEditorWindow()
    win.show()
    sys.exit(app.exec())
