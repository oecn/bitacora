from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QListWidgetItem, QSizePolicy

from widgets import NoteItemWidget


class ViewControllerMixin:
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

    def collapse_all(self):
        rows = self.filtered_rows()
        children_map, _, _, _ = self.build_children_map(rows)
        self.collapsed_parents = set(children_map.keys())
        self.refresh_entries_list()

    def expand_all(self):
        self.collapsed_parents = set()
        self.refresh_entries_list()

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


class EntryControllerMixin:
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
