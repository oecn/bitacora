import os

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMainWindow

from controllers import EntryControllerMixin, ViewControllerMixin
from data_store import DataStoreMixin
from persistence import PersistenceMixin
from theme import apply_theme
from ui_builder import UiBuilderMixin


class MainWindow(
    QMainWindow,
    UiBuilderMixin,
    EntryControllerMixin,
    ViewControllerMixin,
    DataStoreMixin,
    PersistenceMixin,
):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Life in Weeks")
        self.week_notes = {}
        self.work_notes = {}
        self.current_week = None
        self.current_entry = None
        self.loading = False
        self.work_tag = None
        self.filter_tag = None
        self.collapsed_parents = set()
        self.next_entry_id = 1
        self.data_path = os.path.join(os.path.dirname(__file__), "life_notes.json")
        self.heatmap_base_color = QColor("#3b7c7a")
        self.heatmap_colors_by_view = {
            "bitacora": "#3b7c7a",
            "trabajo": "#2f3b59",
        }
        self.work_tag_options = [
            ("\U0001F7E2", "Recibido"),
            ("\U0001F534", "Entregado"),
            ("\U0001F6C8", "Info"),
            ("\u26A0\ufe0f", "Muy importante"),
        ]
        self.work_tag_set = {emoji for emoji, _ in self.work_tag_options}
        self.view_mode = "weeks"

        self.setup_ui()
        apply_theme(self)
        self.update_main_color()
        self.update_heatmap_colors()
        self.load_data()
        self.on_view_changed(self.view_combo.currentIndex())
