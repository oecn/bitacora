import json
import os
import sys

from PySide6.QtCore import QDate, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
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
)


class LifeWeeksWidget(QWidget):
    weekSelected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.birth_date = QDate.currentDate().addYears(-30)
        self.today = QDate.currentDate()
        self.years = 80
        self.weeks_per_year = 52
        self.cell = 11
        self.gap = 3
        self.left_gutter = 44
        self.top_gutter = 26
        self.right_gutter = 10
        self.bottom_gutter = 10

        self.color_grid = QColor("#2f2b26")
        self.color_lived = QColor("#3b7c7a")
        self.color_current = QColor("#e07a2f")
        self.color_future = QColor("#f4efe6")
        self.color_selected = QColor("#1f1a15")

        self.entries_mode = False
        self.selected_week = None
        self.week_counts = {}
        self.heatmap_colors = []

        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def sizeHint(self):
        width = (
            self.left_gutter
            + self.right_gutter
            + self.weeks_per_year * (self.cell + self.gap)
            - self.gap
        )
        height = (
            self.top_gutter
            + self.bottom_gutter
            + self.years * (self.cell + self.gap)
            - self.gap
        )
        return QSize(width, height)

    def set_birth_date(self, date_value):
        self.birth_date = date_value
        self.update()

    def set_years(self, years_value):
        self.years = years_value
        self.updateGeometry()
        self.update()

    def set_entries_mode(self, enabled):
        self.entries_mode = enabled
        if enabled and self.selected_week is None:
            self.selected_week = self.weeks_lived()
            self.weekSelected.emit(self.selected_week)
        self.update()

    def set_week_counts(self, counts):
        self.week_counts = counts or {}
        self.update()

    def set_heatmap_colors(self, colors):
        self.heatmap_colors = colors or []
        self.update()

    def select_week(self, week_index):
        if week_index is None:
            return
        max_index = self.years * self.weeks_per_year - 1
        if week_index < 0 or week_index > max_index:
            return
        self.selected_week = week_index
        self.weekSelected.emit(week_index)
        self.update()

    def weeks_lived(self):
        if self.birth_date > self.today:
            return 0
        days = self.birth_date.daysTo(self.today)
        weeks = days // 7
        max_weeks = self.years * self.weeks_per_year
        if weeks < 0:
            return 0
        if weeks > max_weeks:
            return max_weeks
        return weeks

    def week_at(self, pos):
        x = pos.x() - self.left_gutter
        y = pos.y() - self.top_gutter
        if x < 0 or y < 0:
            return None
        col = int(x // (self.cell + self.gap))
        row = int(y // (self.cell + self.gap))
        if col < 0 or col >= self.weeks_per_year:
            return None
        if row < 0 or row >= self.years:
            return None
        return row * self.weeks_per_year + col

    def mousePressEvent(self, event):
        if not self.entries_mode:
            return
        self.setFocus()
        pos = event.position() if hasattr(event, "position") else event.pos()
        index = self.week_at(pos)
        if index is not None:
            self.select_week(index)
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if not self.entries_mode:
            super().keyPressEvent(event)
            return
        if self.selected_week is None:
            self.select_week(self.weeks_lived())
            return
        row = self.selected_week // self.weeks_per_year
        col = self.selected_week % self.weeks_per_year
        key = event.key()
        if key == Qt.Key_Left:
            col = max(0, col - 1)
        elif key == Qt.Key_Right:
            col = min(self.weeks_per_year - 1, col + 1)
        elif key == Qt.Key_Up:
            row = max(0, row - 1)
        elif key == Qt.Key_Down:
            row = min(self.years - 1, row + 1)
        else:
            super().keyPressEvent(event)
            return
        self.select_week(row * self.weeks_per_year + col)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        grid_pen = QPen(self.color_grid, 1)
        current_pen = QPen(self.color_current, 1)
        selected_pen = QPen(self.color_selected, 1)
        grid_pen.setCosmetic(True)
        current_pen.setCosmetic(True)
        selected_pen.setCosmetic(True)

        weeks_lived = self.weeks_lived()

        label_font = QFont("Segoe UI", 8, QFont.DemiBold)
        painter.setFont(label_font)
        painter.setPen(QPen(self.color_grid, 1))

        month_font = QFont("Segoe UI", 7, QFont.DemiBold)
        painter.setFont(month_font)
        last_month = None
        for col in range(self.weeks_per_year):
            date_value = self.birth_date.addDays(col * 7)
            month = date_value.month()
            if last_month is None or month != last_month:
                x = self.left_gutter + col * (self.cell + self.gap)
                painter.drawText(x, 12, date_value.toString("MMM"))
                last_month = month

        painter.setFont(label_font)
        for year in range(0, self.years, 5):
            y = self.top_gutter + year * (self.cell + self.gap)
            painter.drawText(2, y + self.cell, f"{year:02d}")

        for row in range(self.years):
            for col in range(self.weeks_per_year):
                index = row * self.weeks_per_year + col
                x = self.left_gutter + col * (self.cell + self.gap)
                y = self.top_gutter + row * (self.cell + self.gap)
                rect = QRectF(x, y, self.cell, self.cell)
                border_rect = QRectF(x + 0.5, y + 0.5, self.cell - 1, self.cell - 1)

                count = self.week_counts.get(index, 0)
                if self.entries_mode and self.heatmap_colors:
                    if count > 0:
                        tone_index = min(count, len(self.heatmap_colors) - 1)
                        painter.fillRect(rect, self.heatmap_colors[tone_index])
                    painter.setPen(grid_pen)
                    painter.drawRect(border_rect)
                else:
                    if index < weeks_lived:
                        painter.fillRect(rect, self.color_lived)
                        painter.setPen(grid_pen)
                        painter.drawRect(border_rect)
                    elif index == weeks_lived:
                        painter.fillRect(rect, self.color_future)
                        painter.setPen(grid_pen)
                        painter.drawRect(border_rect)
                    else:
                        painter.setPen(grid_pen)
                        painter.drawRect(border_rect)
                if index == weeks_lived:
                    painter.setPen(current_pen)
                    painter.drawRect(border_rect.adjusted(1, 1, -1, -1))
                    painter.setPen(grid_pen)
                if self.selected_week == index:
                    painter.setPen(selected_pen)
                    painter.drawRect(border_rect.adjusted(1, 1, -1, -1))
                    painter.setPen(grid_pen)


class LegendItem(QFrame):
    def __init__(self, color, text, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        swatch = QFrame(self)
        swatch.setFixedSize(12, 12)
        swatch.setStyleSheet(
            f"background-color: {color}; border: 1px solid #2b2b2b;"
        )
        label = QLabel(text, self)
        label.setStyleSheet("color: #2b2b2b;")

        layout.addWidget(swatch)
        layout.addWidget(label)


class NoteItemWidget(QFrame):
    def __init__(self, date_value, title, subtitle, parent=None):
        super().__init__(parent)
        self.setObjectName("noteItem")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        month = date_value.toString("MMM").upper()
        day = date_value.toString("d")

        date_box = QFrame(self)
        date_box.setObjectName("noteDateBox")
        date_box.setFixedSize(64, 64)
        date_layout = QVBoxLayout(date_box)
        date_layout.setContentsMargins(6, 6, 6, 6)
        date_layout.setSpacing(0)

        month_label = QLabel(month, date_box)
        month_label.setObjectName("noteMonth")
        day_label = QLabel(day, date_box)
        day_label.setObjectName("noteDay")
        month_label.setAlignment(Qt.AlignCenter)
        day_label.setAlignment(Qt.AlignCenter)
        month_label.setFont(QFont("Segoe UI", 8, QFont.DemiBold))
        day_label.setFont(QFont("Segoe UI", 18, QFont.Bold))

        date_layout.addWidget(month_label, alignment=Qt.AlignCenter)
        date_layout.addWidget(day_label, alignment=Qt.AlignCenter)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        emoji, clean_title = self.split_title_emoji(title)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)
        if emoji:
            emoji_label = QLabel(emoji, self)
            emoji_label.setFont(QFont("Segoe UI Emoji", 11))
            emoji_label.setFixedSize(20, 20)
            emoji_label.setAlignment(Qt.AlignCenter)
            title_row.addWidget(emoji_label)
        title_label = QLabel(clean_title, self)
        title_label.setObjectName("noteTitle")
        title_label.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_row.addWidget(title_label, 1)
        subtitle_label = QLabel(subtitle, self)
        subtitle_label.setObjectName("noteSubtitle")

        text_box.addLayout(title_row)
        text_box.addWidget(subtitle_label)

        layout.addWidget(date_box)
        layout.addLayout(text_box, 1)

    def split_title_emoji(self, title):
        if not title:
            return "", ""
        value = title.strip()
        if len(value) >= 2 and value[1] == " ":
            emoji = value[0]
            return emoji, value[2:].lstrip()
        return "", value


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
        self.data_path = os.path.join(os.path.dirname(__file__), "life_notes.json")
        self.heatmap_base_color = QColor("#3b7c7a")
        self.heatmap_colors_by_view = {
            "bitacora": "#3b7c7a",
            "trabajo": "#2f3b59",
        }

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

        controls.addWidget(birth_label)
        controls.addWidget(self.birth_input)
        controls.addSpacing(12)
        controls.addWidget(years_label)
        controls.addWidget(self.years_input)
        controls.addSpacing(12)
        controls.addWidget(view_label)
        controls.addWidget(self.view_combo)
        controls.addStretch(1)

        heatmap_controls = QHBoxLayout()
        heatmap_controls.setSpacing(8)
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
        heatmap_controls.addWidget(self.heatmap_label)
        heatmap_controls.addWidget(self.heatmap_combo)
        heatmap_controls.addWidget(self.heatmap_preview)
        heatmap_controls.addStretch(1)

        root_layout.addLayout(controls)
        root_layout.addLayout(heatmap_controls)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        self.notes_panel = QWidget(self)
        notes_layout = QVBoxLayout(self.notes_panel)
        notes_layout.setContentsMargins(12, 12, 12, 12)
        notes_layout.setSpacing(10)

        notes_title = QLabel("Bitacora", self.notes_panel)
        notes_title.setStyleSheet("font-weight: bold; color: #111111;")
        self.week_label = QLabel("Semana seleccionada: -", self.notes_panel)
        self.week_label.setStyleSheet("color: #2b2b2b;")

        notes_list_label = QLabel("Bitacoras guardadas", self.notes_panel)
        notes_list_label.setStyleSheet("color: #2b2b2b;")
        self.notes_list = QListWidget(self.notes_panel)
        self.notes_list.setSpacing(10)
        self.notes_list.setMinimumWidth(240)
        self.notes_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        notes_layout.addWidget(notes_title)
        notes_layout.addWidget(self.week_label)
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
        self.work_tag_options = [
            ("🟢", "Recibido"),
            ("🔴", "Entregado"),
            ("🛈", "Info"),
            ("⚠️", "Muy importante"),
        ]
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

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        buttons_layout.setContentsMargins(0, 8, 0, 0)
        self.new_button = QPushButton("Nueva bitacora", detail_panel)
        self.save_button = QPushButton("Guardar cambios", detail_panel)
        self.delete_button = QPushButton("Eliminar", detail_panel)
        self.delete_button.setObjectName("dangerButton")
        self.new_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.delete_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.delete_button)

        detail_layout.addWidget(title_label)
        detail_layout.addWidget(self.title_input)
        detail_layout.addWidget(self.work_tag_row)
        detail_layout.addWidget(desc_label)
        detail_layout.addWidget(self.desc_edit, 1)
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

        content_layout.addWidget(self.scroll, 0)
        self.notes_panel.setFixedWidth(660)
        content_layout.addWidget(self.notes_panel)

        root_layout.addLayout(content_layout, 1)

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
        self.delete_button.clicked.connect(self.delete_entry)
        self.notes_list.currentItemChanged.connect(self.on_entry_selected)

        self.apply_theme()
        self.update_heatmap_colors()
        self.load_data()
        self.on_view_changed(self.view_combo.currentIndex())

    def apply_theme(self):
        self.setStyleSheet(
            "QWidget { background: #f3efe6; color: #111111; }"
            "QLabel { font-size: 10pt; }"
            "QDateEdit, QSpinBox {"
            "  background: #ffffff;"
            "  padding: 6px 8px;"
            "  border: 1px solid #1f1f1f;"
            "  border-radius: 6px;"
            "}"
            "QComboBox {"
            "  background: #ffffff;"
            "  padding: 6px 8px;"
            "  border: 1px solid #1f1f1f;"
            "  border-radius: 6px;"
            "}"
            "QTextEdit {"
            "  background: #ffffff;"
            "  border: 1px solid #1f1f1f;"
            "  border-radius: 6px;"
            "}"
            "QLineEdit {"
            "  background: #ffffff;"
            "  border: 1px solid #1f1f1f;"
            "  border-radius: 6px;"
            "  padding: 6px 8px;"
            "  min-height: 28px;"
            "}"
            "QListWidget {"
            "  background: #ffffff;"
            "  border: 1px solid #1f1f1f;"
            "  border-radius: 6px;"
            "}"
            "QPushButton {"
            "  background: #111111;"
            "  color: #ffffff;"
            "  padding: 8px 12px;"
            "  border-radius: 6px;"
            "}"
        )
        self.notes_panel.setStyleSheet(
            "QWidget { background: #ffffff; color: #111111; }"
            "QLabel { font-size: 10pt; }"
            "#detailLabel { color: #4b4b4b; }"
            "QTextEdit {"
            "  background: #ffffff;"
            "  color: #111111;"
            "  border: 1px solid #d3cbbb;"
            "  border-radius: 8px;"
            "}"
            "QLineEdit {"
            "  background: #ffffff;"
            "  color: #111111;"
            "  border: 1px solid #d3cbbb;"
            "  border-radius: 8px;"
            "  padding: 6px 8px;"
            "  min-height: 28px;"
            "}"
            "QListWidget {"
            "  background: #ffffff;"
            "  border: none;"
            "}"
            "#detailPanel {"
            "  background: #faf6ee;"
            "  border: 1px solid #e1d8c8;"
            "  border-radius: 10px;"
            "}"
            "#noteItem {"
            "  background: #ffffff;"
            "  border: 1px solid #e1d8c8;"
            "  border-radius: 10px;"
            "}"
            "#noteDateBox {"
            "  background: #9c2f1d;"
            "  border: 1px solid #6f1f14;"
            "  border-radius: 8px;"
            "  min-width: 64px;"
            "  min-height: 64px;"
            "}"
            "#noteMonth {"
            "  color: #ffffff;"
            "  background: transparent;"
            "  font-size: 8pt;"
            "  letter-spacing: 1px;"
            "}"
            "#noteDay {"
            "  color: #ffffff;"
            "  background: transparent;"
            "  font-size: 18pt;"
            "  font-weight: bold;"
            "}"
            "#noteTitle {"
            "  color: #111111;"
            "  font-weight: bold;"
            "  padding-top: 2px;"
            "}"
            "#noteSubtitle {"
            "  color: #6a6358;"
            "  font-size: 9pt;"
            "}"
            "QPushButton {"
            "  background: #1d2b3a;"
            "  color: #ffffff;"
            "  padding: 8px 10px;"
            "  border-radius: 10px;"
            "  margin: 0 2px;"
            "}"
            "QPushButton#dangerButton {"
            "  background: #a33a2a;"
            "}"
        )

    def on_view_changed(self, index):
        entries_mode = index in (1, 2)
        self.current_entry = None
        self.notes_panel.setVisible(entries_mode)
        self.life_widget.set_entries_mode(entries_mode)
        self.heatmap_label.setVisible(entries_mode)
        self.heatmap_combo.setVisible(entries_mode)
        self.heatmap_preview.setVisible(entries_mode)
        if entries_mode:
            self.sync_heatmap_combo()
            self.update_heatmap_colors()
            self.update_week_counts()
            self.on_week_selected(self.life_widget.selected_week)
        else:
            self.life_widget.set_week_counts({})
        self.heatmap_legend.setVisible(entries_mode)
        self.work_tag_row.setVisible(self.current_view() == "trabajo")

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
                self.select_entry_item(0)
            else:
                self.select_entry_item(self.current_entry)
        else:
            self.select_entry_item(None)

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

    def create_entry(self):
        if self.current_week is None:
            selected = self.life_widget.selected_week
            if selected is None:
                selected = self.life_widget.weeks_lived()
                self.life_widget.select_week(selected)
            self.current_week = selected
        entries = self.current_notes().setdefault(self.current_week, [])
        entry_date = QDate.currentDate().toString("yyyy-MM-dd")
        title = "Nueva bitacora"
        if self.current_view() == "trabajo" and self.work_tag:
            title = f"{self.work_tag} {title}"
        entry = {"title": title, "description": "", "date": entry_date}
        entries.append(entry)
        self.refresh_entries_list()
        self.update_week_counts()
        self.select_entry_item(len(entries) - 1)
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
            entry_date = QDate.currentDate().toString("yyyy-MM-dd")
            entries.append(
                {"title": title, "description": description, "date": entry_date}
            )
            self.current_entry = len(entries) - 1
        else:
            if self.current_entry < 0 or self.current_entry >= len(entries):
                return
            existing = entries[self.current_entry]
            entry_date = existing.get("date") or self.week_entry_date(self.current_week)
            entries[self.current_entry] = {
                "title": title,
                "description": description,
                "date": entry_date,
            }
        self.refresh_entries_list()
        self.update_week_counts()
        self.select_entry_item(self.current_entry)
        self.save_data()

    def delete_entry(self):
        if self.current_week is None or self.current_entry is None:
            return
        entries = self.entries_for_week(self.current_week)
        if 0 <= self.current_entry < len(entries):
            entries.pop(self.current_entry)
        if not entries:
            self.current_notes().pop(self.current_week, None)
            self.current_entry = None
        else:
            self.current_entry = max(0, self.current_entry - 1)
        self.refresh_entries_list()
        self.update_week_counts()
        self.select_entry_item(self.current_entry)
        self.save_data()

    def refresh_entries_list(self):
        self.notes_list.blockSignals(True)
        self.notes_list.clear()
        if self.current_week is None:
            self.clear_entry_form()
            self.notes_list.blockSignals(False)
            return
        entries = self.entries_for_week(self.current_week)
        for index, entry in enumerate(entries):
            title = entry.get("title", "Bitacora") or "Bitacora"
            subtitle = entry.get("description", "")
            subtitle = subtitle.replace("\n", " ").strip() or "Sin detalles"
            if len(subtitle) > 40:
                subtitle = subtitle[:40].rstrip() + "..."
            date_text = entry.get("date", "")
            date_value = QDate.fromString(str(date_text), "yyyy-MM-dd")
            if not date_value.isValid():
                date_value = QDate.fromString(
                    self.week_entry_date(self.current_week), "yyyy-MM-dd"
                )
                if not date_value.isValid():
                    date_value = QDate.currentDate()
            item = QListWidgetItem(self.notes_list)
            item.setData(Qt.UserRole, (self.current_week, index))
            widget = NoteItemWidget(date_value, title, subtitle, self.notes_list)
            item.setSizeHint(widget.sizeHint())
            self.notes_list.setItemWidget(item, widget)
        self.notes_list.blockSignals(False)

    def select_entry_item(self, entry_index):
        self.current_entry = None
        if entry_index is None:
            self.clear_entry_form()
            return
        for row in range(self.notes_list.count()):
            item = self.notes_list.item(row)
            data = item.data(Qt.UserRole)
            if data and data[1] == entry_index:
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
        entries = self.entries_for_week(week_index)
        if 0 <= entry_index < len(entries):
            entry = entries[entry_index]
            self.current_entry = entry_index
            self.title_input.setText(entry.get("title", ""))
            self.desc_edit.setPlainText(entry.get("description", ""))
        if self.current_week != week_index:
            self.life_widget.select_week(week_index)

    def clear_entry_form(self):
        self.title_input.setText("")
        self.desc_edit.setPlainText("")
        self.work_tag = None

    def update_week_counts(self):
        counts = {}
        for week_index, entries in self.current_notes().items():
            if isinstance(entries, list):
                counts[week_index] = len(entries)
        self.life_widget.set_week_counts(counts)

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

    def week_entry_date(self, week_index):
        if week_index is None:
            return QDate.currentDate().toString("yyyy-MM-dd")
        date_value = self.life_widget.birth_date.addDays(week_index * 7)
        return date_value.toString("yyyy-MM-dd")

    def update_scroll_width(self):
        widget_width = self.life_widget.sizeHint().width()
        scrollbar_width = self.scroll.verticalScrollBar().sizeHint().width()
        self.scroll.setFixedWidth(widget_width + scrollbar_width + 6)

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
                        if title or desc:
                            entries.append(
                                {
                                    "title": title or "Entrada",
                                    "description": desc,
                                    "date": date_text,
                                }
                            )
                    if entries:
                        cleaned[week_index] = entries
                elif isinstance(value, str) and value.strip():
                    lines = [line.strip() for line in value.splitlines() if line.strip()]
                    title = lines[0] if lines else "Entrada"
                    desc = "\n".join(lines[1:]) if len(lines) > 1 else ""
                    cleaned[week_index] = [
                        {
                            "title": title,
                            "description": desc,
                            "date": self.week_entry_date(week_index),
                        }
                    ]
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
                        if title or desc:
                            entries.append(
                                {
                                    "title": title or "Bitacora",
                                    "description": desc,
                                    "date": date_text,
                                }
                            )
                    if entries:
                        cleaned_work[week_index] = entries
            self.work_notes = cleaned_work
        self.loading = False
        self.refresh_entries_list()
        self.update_week_counts()

    def save_data(self):
        data = {
            "birth_date": self.birth_input.date().toString("yyyy-MM-dd"),
            "years": self.years_input.value(),
            "heatmap_color": self.heatmap_colors_by_view.get("bitacora"),
            "heatmap_color_trabajo": self.heatmap_colors_by_view.get("trabajo"),
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
