import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsEllipseItem, QScrollArea,
    QGraphicsPathItem, QGraphicsProxyWidget, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QBrush, QColor, QPainterPath, QFont

from tray.context_popup import ContextPopup
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
        self.action = action
        self.block_id = block_id

        params = FUNCTION_REGISTRY[self.action].get("params")
        self.params = {p: None for p in params}

        self.setBrush(QBrush(QColor("#2b2b2b")))
        self.setPen(QColor("#555555"))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)

        # Title
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setPlainText(f"{self.action}")
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
        self.editor.move_block(self.block_id, direction=-1)


    def move_down(self):
        self.editor.move_block(self.block_id, direction=1)


    def set_result(self, text: str):
        self.result_item.setPlainText(f"Result: {text}")


    def delete_self(self):
        self.editor.remove_block(self.block_id)

    
    def update_id(self, id):
        self.block_id = id
        self.title_item.setPlainText(f"{self.block_id} {self.action}")



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
        self.ordered_blocks_ids = []
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

        # ---------- CANVAS + TASK BAR ---------- #
        canvas_layout = QVBoxLayout()

        self.scene = QGraphicsScene()
        self.scene.selectionChanged.connect(self.on_selection_changed)

        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

        canvas_layout.addWidget(self.view, 1)

        # ----- Task bar -----
        task_bar = QHBoxLayout()
        task_bar.addStretch()  

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save)

        task_bar.addWidget(self.cancel_btn)
        task_bar.addWidget(self.save_btn)

        canvas_layout.addLayout(task_bar)

        layout.addLayout(canvas_layout, 1)

        # ---------- TEST PANEL (SCROLLABLE) ---------- #
        test_container = QWidget()
        test_container.setFixedWidth(300)

        test_scroll = QScrollArea()
        test_scroll.setWidgetResizable(True)
        test_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        test_content = QWidget()
        self.test_layout = QVBoxLayout(test_content)
        self.test_layout.setContentsMargins(8, 8, 8, 8)

        # ---- Title ----
        self.test_title = QLabel("Action Inspector")
        self.test_title.setStyleSheet("font-weight: bold")

        # ---- Selected action ----
        self.test_label = QLabel("No action selected")
        self.test_desc = QLabel("")
        self.test_desc.setWordWrap(True)

        # ---- Params ----
        self.params_container = QVBoxLayout()

        # ---- Context display ----
        self.context_title = QLabel("Context")
        self.context_view = QTextEdit()
        self.context_view.setReadOnly(True)
        self.context_view.setFixedHeight(100)

        # ---- Result ----
        self.test_result = QLabel("")

        # ---- Test button ----
        self.test_btn = QPushButton("Test Action")
        self.test_btn.clicked.connect(self.test_selected)

        # ---- Layout order ----
        self.test_layout.addWidget(self.test_title)
        self.test_layout.addWidget(self.test_label)
        self.test_layout.addWidget(self.test_desc)
        self.test_layout.addSpacing(8)
        self.test_layout.addLayout(self.params_container)
        self.test_layout.addSpacing(8)
        self.test_layout.addWidget(self.context_title)
        self.test_layout.addWidget(self.context_view)
        self.test_layout.addStretch()
        self.test_layout.addWidget(self.test_result)
        self.test_layout.addWidget(self.test_btn)

        test_scroll.setWidget(test_content)

        container_layout = QVBoxLayout(test_container)
        container_layout.addWidget(test_scroll)

        layout.addWidget(test_container)

        # ---------- SIGNALS ---------- #
        self.sidebar.itemDoubleClicked.connect(self.add_block)
        self.scene.selectionChanged.connect(self.on_selection_changed)


    # ---------- LOGIC ---------- #

    def add_block(self, item):
        y = len(self.blocks) * self.BLOCK_SPACING
        block_id = uuid4().hex[:4]
        block = ActionNodeItem(item.text(), y, self, block_id)
        self.scene.addItem(block)

        self.blocks[block_id] = {"block": block, "name": item.text()}
        self.ordered_blocks_ids.append(block_id)
        self.relayout_blocks()
 

    def remove_block(self, block_id):
        block = self.blocks.pop(block_id, None)
        if not block:
            return

        self.scene.removeItem(block["block"])
        self.ordered_blocks_ids.remove(block_id)
        self.relayout_blocks()

        # self.scene.blockSignals(True)
        # self.relayout_blocks()
        # self.scene.blockSignals(False)

        # if block_id in self.context:
        #     del self.context[block_id] # remove data from context

        # print("connections", self.connections)
        # for conn in self.connections:
        #     conn.update_path()


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
            self.context_view.clear()
            self.test_result.setText("")
            return
        
        # Title
        block = items[0]
        action_name = block.action
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

        # Context
        self.set_context(block.block_id)


    def set_context(self, block_id):
        context = self.blocks.get(block_id, {}).get("context")
        text = "\n".join(f"{k}: {v}" for k, v in context.items()) if context else "No context available"
        self.context_view.setPlainText(text)



    def test_selected(self):
        items = self.scene.selectedItems()
        if not items:
            return

        block = items[0]
        block_id = block.block_id 

        action_name = block.action
        params = {
            name: box.text()
            for name, box in self.param_inputs.items()
            if box.text() != ""
        }
        block.params.update(params)
        logger.info(f"[TEST] action: {action_name} | params: {params}")

        result = self.run_action(action_name, params)
        logger.info(f"[TEST] result: {result}")

        self.blocks[block_id]["context"] = result["data"]
        self.set_context(block_id)
        self.test_result.setText("Success" if result["success"] else "Failure")
        logger.info(f"[TEST] context: {result["data"]}")


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
        for idx, block_id in enumerate(self.ordered_blocks_ids):
            block = self.blocks[block_id]["block"]
            block.setPos(0, (idx - 1) * self.BLOCK_SPACING)

        self.rebuild_connections()


    def rebuild_connections(self):
        for conn in self.connections:
            self.scene.removeItem(conn)
        self.connections.clear()

        for i in range(len(self.ordered_blocks_ids) - 1):
            block_1 = self.blocks[self.ordered_blocks_ids[i]]["block"]
            block_2 = self.blocks[self.ordered_blocks_ids[i + 1]]["block"]
            conn = ConnectionItem(block_1, block_2)
            self.scene.addItem(conn)
            self.connections.append(conn)


    def move_block(self, block_id, direction: int):
        idx = self.ordered_blocks_ids.index(block_id)
        new_idx = idx + direction
        self.ordered_blocks_ids.remove(block_id)

        if not (0 <= new_idx < len(self.ordered_blocks_ids)):
            return
        
        self.ordered_blocks_ids.insert(new_idx, block_id)
        self.relayout_blocks()


    def closeEvent(self, event):
        try:
            self.scene.selectionChanged.disconnect(self.on_selection_changed)
        except Exception:
            pass
        super().closeEvent(event)


    def _populate_sidebar(self):
        func_names = list(FUNCTION_REGISTRY.keys())
        self.sidebar.addItems(func_names)


    def cancel(self):
        self.close()


    def save(self):
        data = []

        for idx, block in self.blocks.items():
            data.append({
                "id": idx,
                "action": block.action,
                "params": block.params,
            })

        print("SAVED TEMPLATE:")
        print(data)




# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TemplateEditorWindow()
    win.show()
    sys.exit(app.exec())
