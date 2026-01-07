from PySide6.QtWidgets import QVBoxLayout, QWidget


class BitacoraSoloTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)
        self._layout = layout

    def set_content(self, widget):
        if widget is None:
            return
        if self._layout.count() == 1:
            existing = self._layout.itemAt(0).widget()
            if existing is widget:
                return
            self._layout.takeAt(0)
        if widget.parent() is not self:
            widget.setParent(self)
        self._layout.addWidget(widget)
