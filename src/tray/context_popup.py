from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton



class ContextPopup(QDialog):
    def __init__(self, context: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Context")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        text = QTextEdit()
        text.setReadOnly(True)

        # Pretty print context
        content = "\n".join(
            f"{k} : {v}" for k, v in context.items()
        ) or "Context is empty"

        text.setPlainText(content)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        layout.addWidget(text)
        layout.addWidget(close_btn)