import json
import os
import sys

from PySide6.QtCore import QDate, QDateTime, QTime, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QTabWidget,
)

from bitacorasolo import BitacoraSoloTab
from theme import apply_theme
from widgets import LegendItem, LifeWeeksWidget, NoteItemWidget


class MainWindow(QMainWindow):
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

        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        title = QLabel("LIFE IN WEEKS", self)
        title_font = QFont("Bahnschrift", 22, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #111111; letter-spacing: 2px;")

        subtitle = QLabel("1 box = 1 week | 80 year life", self)
        subtitle.setStyleSheet("color: #3b3b3b;")

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        controls = QHBoxLayout()
        controls.setSpacing(14)

        birth_label = QLabel("Birth date", self)
        self.birth_input = QDateEdit(self)
        self.birth_input.setCalendarPopup(True)
        self.birth_input.setDate(QDate.currentDate().addYears(-30))

        years_label = QLabel("Life years", self)
        self.years_input = QSpinBox(self)
        self.years_input.setRange(1, 120)
        self.years_input.setValue(80)

        view_label = QLabel("View", self)
        self.view_combo = QComboBox(self)
        self.view_combo.addItems(["Normal", "Bitacora", "Trabajo"])
        self.mode_button = QPushButton("Dias", self)
        self.mode_button.setToolTip("Cambiar modo de heatmap")
        self.main_color_label = QLabel("Color semanas", self)
        self.main_color_combo = QComboBox(self)
        main_color_options = [
            ("Teal (actual)", "#3b7c7a"),
            ("Neon Green", "#39ff14"),
            ("Hot Pink", "#ff2d95"),
            ("Electric Blue", "#00b3ff"),
            ("Bright Orange", "#ff6f00"),
            ("Lime", "#b9ff1a"),
            ("Cyan", "#00f5ff"),
        ]
        for name, value in main_color_options:
            self.main_color_combo.addItem(name, value)

        controls.addWidget(birth_label)
        controls.addWidget(self.birth_input)
        controls.addSpacing(12)
        controls.addWidget(years_label)
        controls.addWidget(self.years_input)
        controls.addSpacing(12)
        controls.addWidget(view_label)
        controls.addWidget(self.view_combo)
        controls.addWidget(self.mode_button)
        controls.addWidget(self.main_color_label)
        controls.addWidget(self.main_color_combo)
        controls.addStretch(1)

        self.heatmap_label = QLabel("Color heatmap", self)
        self.heatmap_combo = QComboBox(self)
        self.heatmap_combo.setMinimumWidth(140)
        heatmap_options = [
            ("Teal", "#3b7c7a"),
            ("Navy", "#2f3b59"),
            ("Coral", "#cf5b45"),
            ("Olive", "#6b7c3a"),
            ("Indigo", "#4b3f8c"),
            ("Gold", "#b07b1c"),
            ("GitHub Green", "#40c463"),
        ]
        for name, value in heatmap_options:
            self.heatmap_combo.addItem(name, value)
        default_index = self.heatmap_combo.findData("#40c463")
        if default_index != -1:
            self.heatmap_combo.setCurrentIndex(default_index)
        self.heatmap_preview = QWidget(self)
        preview_layout = QHBoxLayout(self.heatmap_preview)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(4)
        self.heatmap_swatches = []
        for _ in range(5):
            swatch = QFrame(self.heatmap_preview)
            swatch.setFixedSize(16, 16)
            swatch.setFrameShape(QFrame.Box)
            swatch.setLineWidth(1)
            preview_layout.addWidget(swatch)
            self.heatmap_swatches.append(swatch)

        root_layout.addLayout(controls)
        controls.addWidget(self.heatmap_label)
        controls.addWidget(self.heatmap_combo)
        controls.addWidget(self.heatmap_preview)

        self.notes_panel = QWidget(self)
        notes_layout = QVBoxLayout(self.notes_panel)
        notes_layout.setContentsMargins(12, 12, 12, 12)
        notes_layout.setSpacing(10)

        notes_title = QLabel("Bitacora", self.notes_panel)
        notes_title.setStyleSheet("font-weight: bold; color: #111111;")
        self.week_label = QLabel("Semana seleccionada: -", self.notes_panel)
        self.week_label.setStyleSheet("color: #2b2b2b;")

        self.filter_row = QWidget(self.notes_panel)
        filter_layout = QHBoxLayout(self.filter_row)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(6)
        filter_label = QLabel("Filtrar", self.filter_row)
        filter_label.setStyleSheet("color: #2b2b2b;")
        filter_layout.addWidget(filter_label)
        self.filter_tag_buttons = []
        all_button = QPushButton("Todos", self.filter_row)
        all_button.setCheckable(True)
        all_button.setChecked(True)
        all_button.clicked.connect(lambda checked=False: self.set_filter_tag(None))
        filter_layout.addWidget(all_button)
        self.filter_tag_buttons.append((all_button, None))
        for emoji, text in self.work_tag_options:
            button = QPushButton(emoji, self.filter_row)
            button.setToolTip(text)
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, tag=emoji: self.set_filter_tag(tag)
            )
            filter_layout.addWidget(button)
            self.filter_tag_buttons.append((button, emoji))
        filter_layout.addStretch(1)

        self.collapse_row = QWidget(self.notes_panel)
        collapse_layout = QHBoxLayout(self.collapse_row)
        collapse_layout.setContentsMargins(0, 0, 0, 0)
        collapse_layout.setSpacing(6)
        self.collapse_all_button = QPushButton("Contraer todo", self.collapse_row)
        self.expand_all_button = QPushButton("Desplegar todo", self.collapse_row)
        self.collapse_all_button.clicked.connect(self.collapse_all)
        self.expand_all_button.clicked.connect(self.expand_all)
        collapse_layout.addWidget(self.collapse_all_button)
        collapse_layout.addWidget(self.expand_all_button)
        collapse_layout.addStretch(1)

        notes_list_label = QLabel("Bitacoras guardadas", self.notes_panel)
        notes_list_label.setStyleSheet("color: #2b2b2b;")
        self.notes_list = QListWidget(self.notes_panel)
        self.notes_list.setSpacing(10)
        self.notes_list.setMinimumWidth(240)
        self.notes_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        notes_layout.addWidget(notes_title)
        notes_layout.addWidget(self.week_label)
        notes_layout.addWidget(self.filter_row)
        notes_layout.addWidget(self.collapse_row)
        notes_layout.addWidget(notes_list_label)

        entries_layout = QHBoxLayout()
        entries_layout.setSpacing(14)
        entries_layout.setContentsMargins(0, 0, 0, 0)
        entries_layout.setAlignment(Qt.AlignTop)
        entries_layout.addWidget(self.notes_list, 1)

        detail_panel = QFrame(self.notes_panel)
        detail_panel.setObjectName("detailPanel")
        detail_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(6, 10, 6, 10)
        detail_layout.setSpacing(8)

        title_label = QLabel("Titulo", detail_panel)
        title_label.setObjectName("detailLabel")
        self.title_input = QLineEdit(detail_panel)
        self.title_input.setPlaceholderText("Titulo de la bitacora")

        self.work_tag_row = QWidget(detail_panel)
        work_tag_layout = QHBoxLayout(self.work_tag_row)
        work_tag_layout.setContentsMargins(0, 0, 0, 0)
        work_tag_layout.setSpacing(6)
        work_tag_label = QLabel("Tipo", self.work_tag_row)
        work_tag_label.setObjectName("detailLabel")
        work_tag_layout.addWidget(work_tag_label)
        self.work_tag_buttons = []
        for emoji, text in self.work_tag_options:
            button = QPushButton(emoji, self.work_tag_row)
            button.setToolTip(text)
            button.setFixedSize(36, 28)
            button.setMinimumHeight(28)
            button.clicked.connect(
                lambda checked=False, tag=emoji: self.set_work_tag(tag)
            )
            work_tag_layout.addWidget(button)
            self.work_tag_buttons.append(button)
        work_tag_layout.addStretch(1)

        desc_label = QLabel("Descripcion", detail_panel)
        desc_label.setObjectName("detailLabel")
        self.desc_edit = QTextEdit(detail_panel)
        self.desc_edit.setPlaceholderText("Escribe la descripcion de la bitacora.")

        related_label = QLabel("Relacionadas", detail_panel)
        related_label.setObjectName("detailLabel")
        self.related_list = QListWidget(detail_panel)
        self.related_list.setSpacing(6)
        self.related_list.setMinimumHeight(90)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        buttons_layout.setContentsMargins(0, 8, 0, 0)
        self.new_button = QPushButton("Nueva bitacora", detail_panel)
        self.save_button = QPushButton("Guardar cambios", detail_panel)
        self.followup_button = QPushButton("Accion tomada", detail_panel)
        self.delete_button = QPushButton("Eliminar", detail_panel)
        self.delete_button.setObjectName("dangerButton")
        self.new_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.followup_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.delete_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.followup_button.setEnabled(False)
        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.followup_button)
        buttons_layout.addWidget(self.delete_button)

        detail_layout.addWidget(title_label)
        detail_layout.addWidget(self.title_input)
        detail_layout.addWidget(self.work_tag_row)
        detail_layout.addWidget(desc_label)
        detail_layout.addWidget(self.desc_edit, 1)
        detail_layout.addWidget(related_label)
        detail_layout.addWidget(self.related_list)
        detail_layout.addLayout(buttons_layout)

        detail_panel.setMinimumWidth(380)
        entries_layout.addWidget(detail_panel, 2)
        entries_layout.setStretch(0, 2)
        entries_layout.setStretch(1, 3)
        notes_layout.addLayout(entries_layout, 1)

        self.life_widget = LifeWeeksWidget(self)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(False)
        self.scroll.setWidget(self.life_widget)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.scroll.setStyleSheet("background: #f6f2ea;")
        self.update_scroll_width()
        self.notes_panel.setFixedWidth(660)

        self.tabs = QTabWidget(self)
        self.calendar_tab = QWidget(self.tabs)
        self.calendar_layout = QHBoxLayout(self.calendar_tab)
        self.calendar_layout.setSpacing(10)
        self.calendar_layout.addWidget(self.scroll, 0)
        self.calendar_layout.addWidget(self.notes_panel)
        self.solo_tab = BitacoraSoloTab(self.tabs)
        self.tabs.addTab(self.calendar_tab, "Calendario")
        self.tabs.addTab(self.solo_tab, "Bitacora")
        root_layout.addWidget(self.tabs, 1)

        self.heatmap_legend = QWidget(self)
        legend_layout = QHBoxLayout(self.heatmap_legend)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(8)
        less_label = QLabel("Less", self.heatmap_legend)
        less_label.setStyleSheet("color: #2b2b2b;")
        more_label = QLabel("More", self.heatmap_legend)
        more_label.setStyleSheet("color: #2b2b2b;")
        legend_layout.addWidget(less_label)
        self.heatmap_legend_swatches = []
        for _ in range(5):
            swatch = QFrame(self.heatmap_legend)
            swatch.setFixedSize(12, 12)
            swatch.setFrameShape(QFrame.Box)
            swatch.setLineWidth(1)
            legend_layout.addWidget(swatch)
            self.heatmap_legend_swatches.append(swatch)
        legend_layout.addWidget(more_label)
        legend_layout.addStretch(1)
        root_layout.addWidget(self.heatmap_legend)

        self.birth_input.dateChanged.connect(self.on_birth_changed)
        self.years_input.valueChanged.connect(self.on_years_changed)
        self.view_combo.currentIndexChanged.connect(self.on_view_changed)
        self.heatmap_combo.currentIndexChanged.connect(self.on_heatmap_color_changed)
        self.life_widget.weekSelected.connect(self.on_week_selected)
        self.new_button.clicked.connect(self.create_entry)
        self.save_button.clicked.connect(self.save_entry)
        self.followup_button.clicked.connect(self.create_followup_entry)
        self.delete_button.clicked.connect(self.delete_entry)
        self.notes_list.currentItemChanged.connect(self.on_entry_selected)
        self.related_list.itemClicked.connect(self.on_related_clicked)
        self.mode_button.clicked.connect(self.toggle_heatmap_mode)
        self.main_color_combo.currentIndexChanged.connect(
            self.on_main_color_changed
        )
        self.tabs.currentChanged.connect(self.on_tab_changed)

        apply_theme(self)
        self.update_main_color()
        self.update_heatmap_colors()
        self.load_data()
        self.on_view_changed(self.view_combo.currentIndex())

    def on_view_changed(self, index):
        if self.is_solo_view() and index == 0:
            self.view_combo.blockSignals(True)
            self.view_combo.setCurrentIndex(1)
            self.view_combo.blockSignals(False)
            index = 1
        entries_mode = index in (1, 2)
        solo_mode = self.is_solo_view()
        self.current_entry = None
        self.notes_panel.setVisible(True)
        self.life_widget.set_entries_mode(entries_mode)
        self.heatmap_label.setVisible(entries_mode and not solo_mode)
        self.heatmap_combo.setVisible(entries_mode and not solo_mode)
        self.heatmap_preview.setVisible(entries_mode and not solo_mode)
        self.mode_button.setVisible(not solo_mode)
        self.main_color_label.setVisible(not entries_mode)
        self.main_color_combo.setVisible(not entries_mode)
        if entries_mode:
            self.sync_heatmap_combo()
            self.update_heatmap_colors()
            self.update_counts()
            if self.is_solo_view():
                self.week_label.setText("Bitacora completa")
                self.refresh_entries_list()
            else:
                self.on_week_selected(self.life_widget.selected_week)
        else:
            self.life_widget.set_week_counts({})
            self.life_widget.set_day_counts({})
            if self.life_widget.selected_week is None:
                self.life_widget.select_week(self.life_widget.weeks_lived())
            self.on_week_selected(self.life_widget.selected_week)
        self.heatmap_legend.setVisible(entries_mode and not solo_mode)
        self.work_tag_row.setVisible(self.current_view() == "trabajo")
        show_filter = self.current_view() == "trabajo"
        self.filter_row.setVisible(show_filter)
        self.collapse_row.setVisible(True)
        if not show_filter and self.filter_tag is not None:
            self.filter_tag = None
        self.update_filter_buttons()

    def is_solo_view(self):
        return self.tabs.currentIndex() == 1

    def move_notes_panel(self, target_layout, target_parent):
        if self.notes_panel.parent() is target_parent:
            return
        self.notes_panel.setParent(target_parent)
        target_layout.addWidget(self.notes_panel)

    def on_tab_changed(self, index):
        if index == 1:
            if self.view_combo.currentIndex() == 0:
                self.view_combo.setCurrentIndex(1)
            self.notes_panel.setMinimumWidth(660)
            self.notes_panel.setMaximumWidth(16777215)
            self.notes_panel.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.solo_tab.set_content(self.notes_panel)
        else:
            self.notes_panel.setFixedWidth(660)
            self.notes_panel.setMaximumWidth(660)
            self.notes_panel.setSizePolicy(
                QSizePolicy.Fixed, QSizePolicy.Expanding
            )
            self.move_notes_panel(self.calendar_layout, self.calendar_tab)
        self.on_view_changed(self.view_combo.currentIndex())

    def on_birth_changed(self, date_value):
        self.life_widget.set_birth_date(date_value)
        self.refresh_entries_list()
        if self.life_widget.selected_week is not None:
            self.on_week_selected(self.life_widget.selected_week)
        if not self.loading:
            self.save_data()

    def on_years_changed(self, years_value):
        self.life_widget.set_years(years_value)
        self.update_scroll_width()
        self.refresh_entries_list()
        if self.life_widget.selected_week is not None:
            self.on_week_selected(self.life_widget.selected_week)
        if not self.loading:
            self.save_data()

    def week_label_text(self, week_index):
        if week_index is None:
            return "Semana seleccionada: -"
        if (
            self.life_widget.view_mode == "days"
            and self.life_widget.selected_date is not None
            and self.life_widget.selected_date.isValid()
        ):
            date_text = self.life_widget.selected_date.toString("yyyy-MM-dd")
            return f"Fecha seleccionada: {date_text}"
        week_number = week_index + 1
        date_value = self.life_widget.birth_date.addDays(week_index * 7)
        date_text = date_value.toString("yyyy-MM-dd")
        return f"Semana {week_number} - {date_text}"

    def on_week_selected(self, week_index):
        if week_index is None:
            return
        self.current_week = week_index
        self.week_label.setText(self.week_label_text(week_index))
        self.refresh_entries_list()
        entries = self.entries_for_week(week_index)
        if entries:
            if self.current_entry is None or self.current_entry >= len(entries):
                self.select_entry_item(0, week_index)
            else:
                self.select_entry_item(self.current_entry, week_index)
        else:
            self.select_entry_item(None, week_index)

    def entries_for_week(self, week_index):
        if week_index is None:
            return []
        return self.current_notes().get(week_index, [])

    def current_notes(self):
        view = self.current_view()
        if view == "trabajo":
            return self.work_notes
        return self.week_notes

    def current_view(self):
        if self.view_combo.currentIndex() == 2:
            return "trabajo"
        return "bitacora"

    def all_entries_for_view(self):
        rows = []
        for week_index, entries in self.current_notes().items():
            if not isinstance(entries, list):
                continue
            for entry_index, entry in enumerate(entries):
                rows.append((week_index, entry_index, entry))
        rows.sort(key=self.entry_date_key, reverse=True)
        return rows

    def entry_date_key(self, row):
        entry = row[2]
        date_text = str(entry.get("date", "")).strip()
        date_value = QDate.fromString(date_text, "yyyy-MM-dd")
        if not date_value.isValid():
            date_value = QDate.fromString(
                self.week_entry_date(row[0]), "yyyy-MM-dd"
            )
        time_text = str(entry.get("time", "")).strip()
        time_value = QTime.fromString(time_text, "HH:mm")
        if not time_value.isValid():
            time_value = QTime(0, 0)
        date_time = QDateTime(date_value, time_value)
        return date_time.toSecsSinceEpoch()

    def clean_links(self, links):
        if not isinstance(links, list):
            return []
        cleaned = []
        for value in links:
            if isinstance(value, int):
                cleaned.append(value)
            elif isinstance(value, str) and value.isdigit():
                cleaned.append(int(value))
        return cleaned

    def ensure_entry_id(self, entry):
        entry_id = entry.get("id")
        if isinstance(entry_id, int) and entry_id > 0:
            if entry_id >= self.next_entry_id:
                self.next_entry_id = entry_id + 1
            return entry_id
        entry_id = self.next_entry_id
        self.next_entry_id += 1
        entry["id"] = entry_id
        return entry_id

    def remove_links_to(self, entry_id):
        if entry_id is None:
            return
        for entries in self.current_notes().values():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                links = entry.get("links")
                if isinstance(links, list) and entry_id in links:
                    entry["links"] = [value for value in links if value != entry_id]

    def find_entry_by_id(self, entry_id):
        if entry_id is None:
            return None
        for week_index, entries in self.current_notes().items():
            if not isinstance(entries, list):
                continue
            for entry_index, entry in enumerate(entries):
                if entry.get("id") == entry_id:
                    return week_index, entry_index, entry
        return None

    def selected_entry_date(self):
        if self.life_widget.view_mode == "days":
            date_value = self.life_widget.selected_date
            if date_value is not None and date_value.isValid():
                return date_value.toString("yyyy-MM-dd")
        return QDate.currentDate().toString("yyyy-MM-dd")

    def current_time_text(self):
        return QTime.currentTime().toString("HH:mm")

    def create_entry(self):
        if self.current_week is None:
            selected = self.life_widget.selected_week
            if selected is None:
                selected = self.life_widget.weeks_lived()
                self.life_widget.select_week(selected)
            self.current_week = selected
        entries = self.current_notes().setdefault(self.current_week, [])
        entry_date = self.selected_entry_date()
        entry_time = self.current_time_text()
        title = "Nueva bitacora"
        if self.current_view() == "trabajo" and self.work_tag:
            title = f"{self.work_tag} {title}"
        entry = {
            "title": title,
            "description": "",
            "date": entry_date,
            "time": entry_time,
            "action": False,
            "links": [],
        }
        self.ensure_entry_id(entry)
        entries.append(entry)
        self.refresh_entries_list()
        self.update_counts()
        self.select_entry_item(len(entries) - 1, self.current_week)
        self.save_data()

    def save_entry(self):
        if self.current_week is None:
            selected = self.life_widget.selected_week
            if selected is None:
                selected = self.life_widget.weeks_lived()
                self.life_widget.select_week(selected)
            self.current_week = selected
        title = self.title_input.text().strip() or "Entrada"
        description = self.desc_edit.toPlainText().strip()
        entries = self.current_notes().setdefault(self.current_week, [])
        if self.current_entry is None:
            entry_date = self.selected_entry_date()
            entry_time = self.current_time_text()
            entries.append(
                {
                    "title": title,
                    "description": description,
                    "date": entry_date,
                    "time": entry_time,
                    "action": False,
                    "links": [],
                }
            )
            self.current_entry = len(entries) - 1
            self.ensure_entry_id(entries[self.current_entry])
        else:
            if self.current_entry < 0 or self.current_entry >= len(entries):
                return
            existing = entries[self.current_entry]
            entry_date = existing.get("date") or self.week_entry_date(self.current_week)
            entry_time = existing.get("time") or self.current_time_text()
            entry_links = self.clean_links(existing.get("links"))
            entry_id = existing.get("id")
            is_action = bool(existing.get("action")) or self.is_action_entry(existing)
            entries[self.current_entry] = {
                "id": entry_id,
                "title": title,
                "description": description,
                "date": entry_date,
                "time": entry_time,
                "action": is_action,
                "links": entry_links,
            }
            self.ensure_entry_id(entries[self.current_entry])
        self.refresh_entries_list()
        self.update_counts()
        self.select_entry_item(self.current_entry, self.current_week)
        self.save_data()

    def delete_entry(self):
        if self.current_week is None or self.current_entry is None:
            return
        entries = self.entries_for_week(self.current_week)
        if 0 <= self.current_entry < len(entries):
            removed = entries.pop(self.current_entry)
            removed_id = removed.get("id") if isinstance(removed, dict) else None
            self.remove_links_to(removed_id)
        if not entries:
            self.current_notes().pop(self.current_week, None)
            self.current_entry = None
        else:
            self.current_entry = max(0, self.current_entry - 1)
        self.refresh_entries_list()
        self.update_counts()
        self.select_entry_item(self.current_entry, self.current_week)
        self.save_data()

    def refresh_entries_list(self):
        self.notes_list.blockSignals(True)
        self.notes_list.clear()
        if self.current_week is None and not self.is_solo_view():
            self.clear_entry_form()
            self.notes_list.blockSignals(False)
            return
        rows = self.filtered_rows()
        children_map, child_ids, id_to_row, entries_by_id = self.build_children_map(rows)

        subtree_cache = {}

        def subtree_max_date(entry_id):
            cached = subtree_cache.get(entry_id)
            if cached is not None:
                return cached
            row = id_to_row.get(entry_id)
            if not row:
                return 0
            max_value = self.entry_date_key(row)
            for child in children_map.get(entry_id, []):
                child_id = child[2].get("id")
                if child_id is not None:
                    max_value = max(max_value, subtree_max_date(child_id))
                else:
                    max_value = max(max_value, self.entry_date_key(child))
            subtree_cache[entry_id] = max_value
            return max_value

        display_rows = []

        def add_row(row, indent_level, has_children, is_child):
            display_rows.append(
                (row[0], row[1], row[2], indent_level, has_children, is_child)
            )

        def add_subtree(entry_id, indent_level):
            row = id_to_row.get(entry_id)
            if not row:
                return
            children = children_map.get(entry_id, [])
            has_children = bool(children)
            add_row(row, indent_level, has_children, indent_level > 0)
            if has_children and entry_id not in self.collapsed_parents:
                children_sorted = sorted(children, key=self.entry_date_key)
                for child in children_sorted:
                    child_id = child[2].get("id")
                    if child_id is not None:
                        add_subtree(child_id, indent_level + 1)
                    else:
                        add_row(child, indent_level + 1, False, True)

        if self.is_solo_view():
            parent_rows = []
            for row in rows:
                entry = row[2]
                entry_id = entry.get("id")
                if entry_id is not None and entry_id in child_ids:
                    continue
                if entry_id is None:
                    parent_rows.append((self.entry_date_key(row), None, row))
                else:
                    parent_rows.append((subtree_max_date(entry_id), entry_id, row))
            parent_rows.sort(key=lambda item: item[0], reverse=True)
            for _, entry_id, row in parent_rows:
                if entry_id is None:
                    add_row(row, 0, False, False)
                else:
                    add_subtree(entry_id, 0)
        else:
            for row in rows:
                entry = row[2]
                entry_id = entry.get("id")
                if entry_id is not None and entry_id in child_ids:
                    continue
                if entry_id is None:
                    add_row(row, 0, False, False)
                else:
                    add_subtree(entry_id, 0)
        entry_ids = []
        id_to_row = {}
        for row_index, row in enumerate(display_rows):
            entry = row[2]
            entry_id = entry.get("id")
            if isinstance(entry_id, int):
                entry_ids.append(entry_id)
                id_to_row[entry_id] = row_index
            else:
                entry_ids.append(None)
        direct_links = {}
        for entry_id, entry in entries_by_id.items():
            links = set(self.clean_links(entry.get("links")))
            direct_links[entry_id] = links
        mutual_links = {}
        for entry_id, links in direct_links.items():
            mutual_links[entry_id] = {
                link_id
                for link_id in links
                if entry_id in direct_links.get(link_id, set())
            }
        connector_palette = [
            "#f5b700",
            "#1f78ff",
            "#2ad54e",
            "#ff4b3a",
            "#8d5bff",
            "#00b3a4",
        ]
        pair_colors = {}
        color_index = 0

        def pair_color(a_id, b_id):
            nonlocal color_index
            pair = tuple(sorted((a_id, b_id)))
            color = pair_colors.get(pair)
            if color:
                return color
            color = connector_palette[color_index % len(connector_palette)]
            color_index += 1
            pair_colors[pair] = color
            return color
        for week_index, index, entry, indent_level, has_children, is_child in display_rows:
            title = entry.get("title", "Bitacora") or "Bitacora"
            subtitle = entry.get("description", "")
            subtitle = subtitle.replace("\n", " ").strip() or "Sin detalles"
            links = self.clean_links(entry.get("links"))
            if links:
                subtitle = f"{subtitle} | Rel: {len(links)}"
            time_text = str(entry.get("time", "")).strip()
            if time_text:
                subtitle = f"{subtitle} | {time_text}"
            if len(subtitle) > 40:
                subtitle = subtitle[:40].rstrip() + "..."
            date_text = entry.get("date", "")
            date_value = QDate.fromString(str(date_text), "yyyy-MM-dd")
            if not date_value.isValid():
                date_value = QDate.fromString(
                    self.week_entry_date(week_index), "yyyy-MM-dd"
                )
            if not date_value.isValid():
                date_value = QDate.currentDate()
            item = QListWidgetItem(self.notes_list)
            item.setData(Qt.UserRole, (week_index, index))
            connector_color = None
            connector_top = False
            connector_bottom = False
            entry_id = entry.get("id")
            if isinstance(entry_id, int):
                row_index = id_to_row.get(entry_id)
                if row_index is not None:
                    prev_entry_id = (
                        entry_ids[row_index - 1] if row_index > 0 else None
                    )
                    next_entry_id = (
                        entry_ids[row_index + 1]
                        if row_index < len(entry_ids) - 1
                        else None
                    )
                    linked_prev = (
                        prev_entry_id in mutual_links.get(entry_id, set())
                        if prev_entry_id is not None
                        else False
                    )
                    linked_next = (
                        next_entry_id in mutual_links.get(entry_id, set())
                        if next_entry_id is not None
                        else False
                    )
                    if linked_prev:
                        connector_top = True
                        connector_color = pair_color(entry_id, prev_entry_id)
                    if linked_next:
                        connector_bottom = True
                        if connector_color is None:
                            connector_color = pair_color(entry_id, next_entry_id)
            widget = NoteItemWidget(
                date_value,
                title,
                subtitle,
                self.notes_list,
                connector_color=connector_color,
                connector_top=connector_top,
                connector_bottom=connector_bottom,
                indent_level=indent_level,
                has_children=has_children,
                collapsed=entry_id in self.collapsed_parents,
                entry_id=entry_id,
            )
            if has_children:
                widget.collapseClicked.connect(self.toggle_parent_collapse)
            item.setSizeHint(widget.sizeHint())
            self.notes_list.setItemWidget(item, widget)
        self.notes_list.blockSignals(False)

    def select_entry_item(self, entry_index, week_index=None):
        self.current_entry = None
        if entry_index is None:
            self.clear_entry_form()
            return
        for row in range(self.notes_list.count()):
            item = self.notes_list.item(row)
            data = item.data(Qt.UserRole)
            if not data:
                continue
            if week_index is None and data[1] == entry_index:
                self.notes_list.setCurrentItem(item)
                self.current_entry = entry_index
                return
            if week_index is not None and data[0] == week_index and data[1] == entry_index:
                self.notes_list.setCurrentItem(item)
                self.current_entry = entry_index
                return
        self.notes_list.setCurrentItem(None)
        self.clear_entry_form()

    def on_entry_selected(self, current, previous):
        if current is None:
            self.current_entry = None
            self.clear_entry_form()
            return
        data = current.data(Qt.UserRole)
        if not data:
            return
        week_index, entry_index = data
        self.current_week = week_index
        entries = self.entries_for_week(week_index)
        if 0 <= entry_index < len(entries):
            entry = entries[entry_index]
            self.current_entry = entry_index
            self.title_input.setText(entry.get("title", ""))
            self.desc_edit.setPlainText(entry.get("description", ""))
            self.refresh_related_list(entry)
            self.followup_button.setEnabled(True)
            if self.life_widget.view_mode == "days":
                date_text = str(entry.get("date", "")).strip()
                date_value = QDate.fromString(date_text, "yyyy-MM-dd")
                if date_value.isValid():
                    self.life_widget.select_date(date_value)
        if not self.is_solo_view() and self.current_week != week_index:
            self.life_widget.select_week(week_index)

    def refresh_related_list(self, entry):
        self.related_list.clear()
        if not isinstance(entry, dict):
            return
        links = self.clean_links(entry.get("links"))
        for link_id in links:
            found = self.find_entry_by_id(link_id)
            if not found:
                continue
            week_index, entry_index, linked_entry = found
            date_text = str(linked_entry.get("date", "")).strip()
            title = linked_entry.get("title", "Entrada") or "Entrada"
            label = f"{date_text} - {title}"
            item = QListWidgetItem(label, self.related_list)
            item.setData(Qt.UserRole, (link_id, week_index, entry_index))

    def on_related_clicked(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        _, week_index, entry_index = data
        if week_index is None:
            return
        if self.is_solo_view():
            self.select_entry_item(entry_index, week_index)
        else:
            self.life_widget.select_week(week_index)
            self.refresh_entries_list()
            self.select_entry_item(entry_index, week_index)

    def create_followup_entry(self):
        if self.current_week is None or self.current_entry is None:
            return
        entries = self.entries_for_week(self.current_week)
        if not (0 <= self.current_entry < len(entries)):
            return
        base_entry = entries[self.current_entry]
        base_id = self.ensure_entry_id(base_entry)
        base_entry["links"] = self.clean_links(base_entry.get("links"))

        entry_date = self.selected_entry_date()
        target_week = self.current_week
        date_value = QDate.fromString(entry_date, "yyyy-MM-dd")
        if date_value.isValid():
            week_index = self.life_widget.week_index_for_date(date_value)
            if week_index is not None:
                target_week = week_index

        title = "Accion tomada"
        if self.current_view() == "trabajo" and self.work_tag:
            title = f"{self.work_tag} {title}"
        entry_time = self.current_time_text()
        new_entry = {
            "title": title,
            "description": "",
            "date": entry_date,
            "time": entry_time,
            "action": True,
            "links": [base_id],
        }
        new_id = self.ensure_entry_id(new_entry)
        target_entries = self.current_notes().setdefault(target_week, [])
        target_entries.append(new_entry)
        if new_id not in base_entry["links"]:
            base_entry["links"].append(new_id)

        self.life_widget.select_week(target_week)
        self.refresh_entries_list()
        self.update_counts()
        self.select_entry_item(len(target_entries) - 1, target_week)
        self.save_data()

    def clear_entry_form(self):
        self.title_input.setText("")
        self.desc_edit.setPlainText("")
        self.related_list.clear()
        self.followup_button.setEnabled(False)
        self.work_tag = None

    def update_week_counts(self):
        counts = {}
        for week_index, entries in self.current_notes().items():
            if isinstance(entries, list):
                counts[week_index] = len(entries)
        self.life_widget.set_week_counts(counts)

    def update_day_counts(self):
        counts = {}
        for entries in self.current_notes().values():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                date_text = str(entry.get("date", "")).strip()
                date_value = QDate.fromString(date_text, "yyyy-MM-dd")
                if not date_value.isValid():
                    continue
                key = date_value.toString("yyyy-MM-dd")
                counts[key] = counts.get(key, 0) + 1
        self.life_widget.set_day_counts(counts)

    def update_counts(self):
        self.update_week_counts()
        self.update_day_counts()

    def update_main_color(self):
        color_value = self.main_color_combo.currentData() or "#3b7c7a"
        self.life_widget.set_main_color(color_value)

    def update_heatmap_colors(self):
        view = self.current_view()
        stored = self.heatmap_colors_by_view.get(view, "#3b7c7a")
        selected = self.heatmap_combo.currentData() or stored
        self.heatmap_colors_by_view[view] = selected
        self.heatmap_base_color = QColor(selected)
        colors = self.build_heatmap_colors(self.heatmap_base_color)
        self.life_widget.set_heatmap_colors(colors)
        for swatch, color in zip(self.heatmap_swatches, colors):
            swatch.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #1f1f1f;"
            )
        for swatch, color in zip(self.heatmap_legend_swatches, colors):
            swatch.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #1f1f1f;"
            )

    def sync_heatmap_combo(self):
        view = self.current_view()
        stored = self.heatmap_colors_by_view.get(view)
        if not stored:
            return
        combo_index = self.heatmap_combo.findData(stored)
        if combo_index == -1:
            return
        self.heatmap_combo.blockSignals(True)
        self.heatmap_combo.setCurrentIndex(combo_index)
        self.heatmap_combo.blockSignals(False)

    def set_work_tag(self, emoji):
        self.work_tag = emoji
        title = self.title_input.text().lstrip()
        for tag, _ in self.work_tag_options:
            if title.startswith(f"{tag} "):
                title = title[len(tag) + 1 :].lstrip()
                break
        if emoji:
            title = f"{emoji} {title}".strip()
        self.title_input.setText(title)

    def entry_tag(self, entry):
        title = str(entry.get("title", "")).strip()
        if len(title) >= 2 and title[1] == " ":
            emoji = title[0]
            if emoji in self.work_tag_set:
                return emoji
        return None

    def set_filter_tag(self, emoji):
        if emoji is not None and emoji not in self.work_tag_set:
            return
        self.filter_tag = emoji
        self.update_filter_buttons()
        self.refresh_entries_list()

    def update_filter_buttons(self):
        for button, tag in self.filter_tag_buttons:
            button.blockSignals(True)
            button.setChecked(tag == self.filter_tag)
            if self.filter_tag is None and tag is None:
                button.setChecked(True)
            button.blockSignals(False)

    def filtered_rows(self):
        if self.is_solo_view():
            rows = self.all_entries_for_view()
        else:
            rows = [
                (self.current_week, index, entry)
                for index, entry in enumerate(self.entries_for_week(self.current_week))
            ]
        if self.current_view() == "trabajo" and self.filter_tag:
            rows = [
                row for row in rows if self.entry_tag(row[2]) == self.filter_tag
            ]
        return rows

    def build_children_map(self, rows):
        id_to_row = {}
        entries_by_id = {}
        for row in rows:
            entry = row[2]
            entry_id = entry.get("id")
            if isinstance(entry_id, int):
                id_to_row[entry_id] = row
                entries_by_id[entry_id] = entry
        children_map = {}
        child_ids = set()
        for row in rows:
            entry = row[2]
            entry_id = entry.get("id")
            parent_id = self.action_parent_id(entry, entries_by_id)
            if parent_id is None or entry_id is None:
                continue
            if parent_id in id_to_row:
                children_map.setdefault(parent_id, []).append(row)
                child_ids.add(entry_id)
        return children_map, child_ids, id_to_row, entries_by_id

    def collapse_all(self):
        rows = self.filtered_rows()
        children_map, _, _, _ = self.build_children_map(rows)
        self.collapsed_parents = set(children_map.keys())
        self.refresh_entries_list()

    def expand_all(self):
        self.collapsed_parents = set()
        self.refresh_entries_list()

    def is_action_entry(self, entry):
        if entry.get("action") is True:
            return True
        title = str(entry.get("title", "")).strip().lower()
        return title.startswith("accion tomada")

    def action_parent_id(self, entry, entries_by_id):
        if not self.is_action_entry(entry):
            return None
        links = self.clean_links(entry.get("links"))
        if not links:
            return None
        parent_id = links[0]
        parent = entries_by_id.get(parent_id)
        if not parent:
            return None
        parent_links = self.clean_links(parent.get("links"))
        if entry.get("id") not in parent_links:
            return None
        return parent_id

    def toggle_parent_collapse(self, entry_id):
        if entry_id in self.collapsed_parents:
            self.collapsed_parents.remove(entry_id)
        else:
            self.collapsed_parents.add(entry_id)
        self.refresh_entries_list()

    def build_heatmap_colors(self, base_color):
        h, s, l, a = base_color.getHsl()
        levels = [
            min(255, int(l + (255 - l) * 0.6)),
            min(255, int(l + (255 - l) * 0.4)),
            l,
            max(0, int(l * 0.8)),
            max(0, int(l * 0.6)),
        ]
        colors = []
        for level in levels:
            tone = QColor()
            tone.setHsl(h, s, level, a)
            colors.append(tone)
        return colors

    def on_heatmap_color_changed(self):
        self.update_heatmap_colors()
        if not self.loading:
            self.save_data()

    def on_main_color_changed(self):
        self.update_main_color()
        if not self.loading:
            self.save_data()

    def week_entry_date(self, week_index):
        if week_index is None:
            return QDate.currentDate().toString("yyyy-MM-dd")
        date_value = self.life_widget.birth_date.addDays(week_index * 7)
        return date_value.toString("yyyy-MM-dd")

    def update_scroll_width(self):
        widget_width = self.life_widget.sizeHint().width()
        scrollbar_width = self.scroll.verticalScrollBar().sizeHint().width()
        self.scroll.setFixedWidth(widget_width + scrollbar_width + 6)

    def toggle_heatmap_mode(self):
        self.view_mode = "days" if self.view_mode == "weeks" else "weeks"
        self.life_widget.set_view_mode(self.view_mode)
        self.mode_button.setText("Semanas" if self.view_mode == "days" else "Dias")
        self.update_scroll_width()
        self.update_counts()
        if self.life_widget.entries_mode:
            self.on_week_selected(self.life_widget.selected_week)

    def load_data(self):
        if not os.path.exists(self.data_path):
            return
        try:
            with open(self.data_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return
        self.loading = True
        heatmap_color = data.get("heatmap_color")
        if isinstance(heatmap_color, str) and heatmap_color.strip():
            combo_index = self.heatmap_combo.findData(heatmap_color.strip())
            if combo_index != -1:
                self.heatmap_combo.setCurrentIndex(combo_index)
            self.heatmap_colors_by_view["bitacora"] = heatmap_color.strip()
        main_color = data.get("main_color")
        if isinstance(main_color, str) and main_color.strip():
            combo_index = self.main_color_combo.findData(main_color.strip())
            if combo_index != -1:
                self.main_color_combo.setCurrentIndex(combo_index)
        work_heatmap = data.get("heatmap_color_trabajo")
        if isinstance(work_heatmap, str) and work_heatmap.strip():
            self.heatmap_colors_by_view["trabajo"] = work_heatmap.strip()
        birth_text = data.get("birth_date")
        if isinstance(birth_text, str):
            birth_date = QDate.fromString(birth_text, "yyyy-MM-dd")
            if birth_date.isValid():
                self.birth_input.setDate(birth_date)
                self.life_widget.set_birth_date(birth_date)
        years_value = data.get("years")
        if isinstance(years_value, int):
            self.years_input.setValue(years_value)
            self.life_widget.set_years(years_value)
        stored_next_id = data.get("next_entry_id")
        if isinstance(stored_next_id, int) and stored_next_id > 0:
            self.next_entry_id = stored_next_id
        notes = data.get("notes", {})
        if isinstance(notes, dict):
            cleaned = {}
            for key, value in notes.items():
                try:
                    week_index = int(key)
                except (TypeError, ValueError):
                    continue
                if isinstance(value, list):
                    entries = []
                    for entry in value:
                        if not isinstance(entry, dict):
                            continue
                        title = str(entry.get("title", "")).strip()
                        desc = str(entry.get("description", "")).strip()
                        date_text = str(entry.get("date", "")).strip()
                        date_value = QDate.fromString(date_text, "yyyy-MM-dd")
                        if not date_value.isValid():
                            date_text = self.week_entry_date(week_index)
                        time_text = str(entry.get("time", "")).strip()
                        time_value = QTime.fromString(time_text, "HH:mm")
                        if not time_value.isValid():
                            time_text = ""
                        links = self.clean_links(entry.get("links"))
                        entry_id = entry.get("id")
                        if title or desc:
                            entry_data = {
                                "title": title or "Entrada",
                                "description": desc,
                                "date": date_text,
                                "time": time_text,
                                "action": entry.get("action") is True,
                                "links": links,
                            }
                            if self.is_action_entry(entry_data):
                                entry_data["action"] = True
                            if isinstance(entry_id, int) and entry_id > 0:
                                entry_data["id"] = entry_id
                            self.ensure_entry_id(entry_data)
                            entries.append(entry_data)
                    if entries:
                        cleaned[week_index] = entries
                elif isinstance(value, str) and value.strip():
                    lines = [line.strip() for line in value.splitlines() if line.strip()]
                    title = lines[0] if lines else "Entrada"
                    desc = "\n".join(lines[1:]) if len(lines) > 1 else ""
                    entry_data = {
                        "title": title,
                        "description": desc,
                        "date": self.week_entry_date(week_index),
                        "time": "",
                        "action": False,
                        "links": [],
                    }
                    self.ensure_entry_id(entry_data)
                    cleaned[week_index] = [entry_data]
            self.week_notes = cleaned
        work_notes = data.get("work_notes", {})
        if isinstance(work_notes, dict):
            cleaned_work = {}
            for key, value in work_notes.items():
                try:
                    week_index = int(key)
                except (TypeError, ValueError):
                    continue
                if isinstance(value, list):
                    entries = []
                    for entry in value:
                        if not isinstance(entry, dict):
                            continue
                        title = str(entry.get("title", "")).strip()
                        desc = str(entry.get("description", "")).strip()
                        date_text = str(entry.get("date", "")).strip()
                        date_value = QDate.fromString(date_text, "yyyy-MM-dd")
                        if not date_value.isValid():
                            date_text = self.week_entry_date(week_index)
                        time_text = str(entry.get("time", "")).strip()
                        time_value = QTime.fromString(time_text, "HH:mm")
                        if not time_value.isValid():
                            time_text = ""
                        links = self.clean_links(entry.get("links"))
                        entry_id = entry.get("id")
                        if title or desc:
                            entry_data = {
                                "title": title or "Bitacora",
                                "description": desc,
                                "date": date_text,
                                "time": time_text,
                                "action": entry.get("action") is True,
                                "links": links,
                            }
                            if self.is_action_entry(entry_data):
                                entry_data["action"] = True
                            if isinstance(entry_id, int) and entry_id > 0:
                                entry_data["id"] = entry_id
                            self.ensure_entry_id(entry_data)
                            entries.append(entry_data)
                    if entries:
                        cleaned_work[week_index] = entries
            self.work_notes = cleaned_work
        self.loading = False
        self.refresh_entries_list()
        self.update_counts()
        self.update_main_color()

    def save_data(self):
        data = {
            "birth_date": self.birth_input.date().toString("yyyy-MM-dd"),
            "years": self.years_input.value(),
            "next_entry_id": self.next_entry_id,
            "heatmap_color": self.heatmap_colors_by_view.get("bitacora"),
            "heatmap_color_trabajo": self.heatmap_colors_by_view.get("trabajo"),
            "main_color": self.main_color_combo.currentData(),
            "notes": {str(k): v for k, v in self.week_notes.items()},
            "work_notes": {str(k): v for k, v in self.work_notes.items()},
        }
        try:
            with open(self.data_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=True, indent=2)
        except OSError:
            return

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1000, 720)
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
