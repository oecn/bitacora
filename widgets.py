from PySide6.QtCore import QDate, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class LifeWeeksWidget(QWidget):
    weekSelected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.birth_date = QDate.currentDate().addYears(-30)
        self.today = QDate.currentDate()
        self.years = 80
        self.weeks_per_year = 52
        self.day_cols = 52
        self.day_rows = 7
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
        self.selected_date = None
        self.week_counts = {}
        self.day_counts = {}
        self.heatmap_colors = []
        self.view_mode = "weeks"

        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def sizeHint(self):
        if self.view_mode == "days":
            width = (
                self.left_gutter
                + self.right_gutter
                + self.day_cols * (self.cell + self.gap)
                - self.gap
            )
            height = (
                self.top_gutter
                + self.bottom_gutter
                + self.day_rows * (self.cell + self.gap)
                - self.gap
            )
        else:
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

    def set_cell_size(self, cell, gap):
        self.cell = cell
        self.gap = gap
        self.updateGeometry()
        self.update()

    def set_view_mode(self, mode):
        if mode not in ("weeks", "days"):
            return
        self.view_mode = mode
        if self.view_mode == "days":
            self.ensure_selected_date()
        self.updateGeometry()
        self.update()

    def set_entries_mode(self, enabled):
        self.entries_mode = enabled
        if enabled and self.selected_week is None:
            self.selected_week = self.weeks_lived()
            self.weekSelected.emit(self.selected_week)
        if enabled and self.view_mode == "days":
            self.ensure_selected_date()
        self.update()

    def set_week_counts(self, counts):
        self.week_counts = counts or {}
        self.update()

    def set_day_counts(self, counts):
        self.day_counts = counts or {}
        self.update()

    def set_heatmap_colors(self, colors):
        self.heatmap_colors = colors or []
        self.update()

    def set_main_color(self, color_value):
        if not color_value:
            return
        base = QColor(color_value)
        if not base.isValid():
            return
        self.color_lived = base
        self.color_current = base.darker(140)
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

    def ensure_selected_date(self):
        start_date = self.daily_start_date()
        end_date = self.daily_end_date()
        if (
            self.selected_date is None
            or not self.selected_date.isValid()
            or self.selected_date < start_date
            or self.selected_date > self.today
        ):
            if self.today < start_date:
                self.selected_date = end_date
            else:
                self.selected_date = self.today

    def select_date(self, date_value):
        if date_value is None or not date_value.isValid():
            return
        start_date = self.daily_start_date()
        end_date = self.daily_end_date()
        if date_value < start_date or date_value > end_date:
            return
        if date_value > self.today:
            return
        self.selected_date = date_value
        self.update()

    def daily_end_date(self):
        days_to_end = 7 - self.today.dayOfWeek()
        return self.today.addDays(days_to_end)

    def daily_start_date(self):
        total_days = self.day_cols * self.day_rows
        return self.daily_end_date().addDays(-(total_days - 1))

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

    def day_at(self, pos):
        x = pos.x() - self.left_gutter
        y = pos.y() - self.top_gutter
        if x < 0 or y < 0:
            return None
        col = int(x // (self.cell + self.gap))
        row = int(y // (self.cell + self.gap))
        if col < 0 or col >= self.day_cols:
            return None
        if row < 0 or row >= self.day_rows:
            return None
        return self.daily_start_date().addDays(col * 7 + row)

    def day_index_for_date(self, date_value):
        if date_value is None or not date_value.isValid():
            return None
        start_date = self.daily_start_date()
        total_days = self.day_cols * self.day_rows
        index = start_date.daysTo(date_value)
        if index < 0 or index >= total_days:
            return None
        return index

    def date_for_day_index(self, index):
        if index is None:
            return None
        total_days = self.day_cols * self.day_rows
        if index < 0 or index >= total_days:
            return None
        return self.daily_start_date().addDays(index)

    def week_index_for_date(self, date_value):
        if date_value is None or not date_value.isValid():
            return None
        if date_value < self.birth_date:
            return None
        days = self.birth_date.daysTo(date_value)
        return max(0, days // 7)

    def mousePressEvent(self, event):
        if not self.entries_mode:
            return
        self.setFocus()
        pos = event.position() if hasattr(event, "position") else event.pos()
        if self.view_mode == "days":
            date_value = self.day_at(pos)
            if date_value is not None:
                if date_value > self.today:
                    return
                self.select_date(date_value)
                week_index = self.week_index_for_date(date_value)
                if week_index is not None:
                    self.select_week(week_index)
                    return
        else:
            index = self.week_at(pos)
            if index is not None:
                self.select_week(index)
                return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if not self.entries_mode:
            super().keyPressEvent(event)
            return
        if self.view_mode == "days":
            self.ensure_selected_date()
            index = self.day_index_for_date(self.selected_date)
            if index is None:
                super().keyPressEvent(event)
                return
            key = event.key()
            if key == Qt.Key_Left:
                index -= self.day_rows
            elif key == Qt.Key_Right:
                index += self.day_rows
            elif key == Qt.Key_Up:
                index -= 1
            elif key == Qt.Key_Down:
                index += 1
            else:
                super().keyPressEvent(event)
                return
            date_value = self.date_for_day_index(index)
            if date_value is None:
                return
            if date_value > self.today:
                return
            self.select_date(date_value)
            week_index = self.week_index_for_date(date_value)
            if week_index is not None:
                self.select_week(week_index)
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
        if self.view_mode == "days":
            self.paint_daily()
            return
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

    def paint_daily(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        grid_pen = QPen(self.color_grid, 1)
        current_pen = QPen(self.color_current, 1)
        selected_pen = QPen(self.color_selected, 1)
        grid_pen.setCosmetic(True)
        current_pen.setCosmetic(True)
        selected_pen.setCosmetic(True)

        start_date = self.daily_start_date()
        month_font = QFont("Segoe UI", 7, QFont.DemiBold)
        painter.setFont(month_font)
        painter.setPen(QPen(self.color_grid, 1))

        last_month = None
        for col in range(self.day_cols):
            date_value = start_date.addDays(col * 7)
            month = date_value.month()
            if last_month is None or month != last_month:
                x = self.left_gutter + col * (self.cell + self.gap)
                painter.drawText(x, 12, date_value.toString("MMM"))
                last_month = month

        day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
        for row in range(self.day_rows):
            day_of_week = ((start_date.dayOfWeek() - 1 + row) % 7) + 1
            label = day_labels.get(day_of_week)
            if label:
                y = self.top_gutter + row * (self.cell + self.gap)
                painter.drawText(6, y + self.cell, label)

        for col in range(self.day_cols):
            for row in range(self.day_rows):
                date_value = start_date.addDays(col * 7 + row)
                key = date_value.toString("yyyy-MM-dd")
                count = self.day_counts.get(key, 0)
                x = self.left_gutter + col * (self.cell + self.gap)
                y = self.top_gutter + row * (self.cell + self.gap)
                rect = QRectF(x, y, self.cell, self.cell)
                border_rect = QRectF(x + 0.5, y + 0.5, self.cell - 1, self.cell - 1)

                if self.entries_mode and self.heatmap_colors and count > 0:
                    tone_index = min(count, len(self.heatmap_colors) - 1)
                    painter.fillRect(rect, self.heatmap_colors[tone_index])
                painter.setPen(grid_pen)
                painter.drawRect(border_rect)

                if date_value == self.today:
                    painter.setPen(current_pen)
                    painter.drawRect(border_rect.adjusted(1, 1, -1, -1))
                    painter.setPen(grid_pen)

                if self.selected_date is not None and date_value == self.selected_date:
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
    collapseClicked = Signal(int)

    def __init__(
        self,
        date_value,
        title,
        subtitle,
        parent=None,
        connector_color=None,
        connector_top=False,
        connector_bottom=False,
        indent_level=0,
        has_children=False,
        collapsed=False,
        entry_id=None,
    ):
        super().__init__(parent)
        self.setObjectName("noteItem")
        self.connector_color = QColor(connector_color) if connector_color else None
        self.connector_top = connector_top
        self.connector_bottom = connector_bottom
        self.entry_id = entry_id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(26 + indent_level * 18, 8, 10, 8)
        layout.setSpacing(10)

        month = date_value.toString("MMM").upper()
        day = date_value.toString("d")

        if has_children:
            toggle_button = QToolButton(self)
            toggle_button.setText("+" if collapsed else "-")
            toggle_button.setFixedSize(18, 18)
            toggle_button.setAutoRaise(True)
            toggle_button.setStyleSheet(
                "QToolButton {"
                "  background: #f0e8dc;"
                "  border: 1px solid #c9b8a6;"
                "  border-radius: 9px;"
                "  font-weight: bold;"
                "}"
            )
            toggle_button.clicked.connect(self.on_toggle_clicked)
            layout.addWidget(toggle_button)
        else:
            spacer = QWidget(self)
            spacer.setFixedSize(18, 18)
            layout.addWidget(spacer)

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

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.connector_color or not self.connector_color.isValid():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self.connector_color, 6, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        center_y = self.height() / 2
        top_y = 6 if self.connector_top else center_y
        bottom_y = self.height() - 6 if self.connector_bottom else center_y
        x = 12
        painter.drawLine(x, top_y, x, bottom_y)
        painter.setBrush(self.connector_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(x - 8), int(center_y - 8), 16, 16)
        painter.setPen(pen)
        painter.drawLine(x, center_y, x + 10, center_y)

    def on_toggle_clicked(self):
        if self.entry_id is None:
            return
        self.collapseClicked.emit(self.entry_id)
