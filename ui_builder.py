from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
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
from widgets import LifeWeeksWidget


class UiBuilderMixin:
    def setup_ui(self):
        central = QWidget(self)
        central.setObjectName("centralRoot")
        central.setStyleSheet(
            "#centralRoot {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "    stop:0 #f6f1e9, stop:1 #ede3d6);"
            "}"
        )
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
        separator = QFrame(self.calendar_tab)
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet("color: #d2c6b7;")
        separator.setLineWidth(1)
        self.calendar_layout.addWidget(separator)
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

        self.apply_panel_shadow(self.notes_panel)
        self.apply_panel_shadow(detail_panel)
        self.apply_panel_shadow(self.scroll)

    def apply_panel_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 70))
        widget.setGraphicsEffect(shadow)
