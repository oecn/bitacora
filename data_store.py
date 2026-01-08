from PySide6.QtCore import QDate, QDateTime, QTime


class DataStoreMixin:
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

    def week_entry_date(self, week_index):
        if week_index is None:
            return QDate.currentDate().toString("yyyy-MM-dd")
        date_value = self.life_widget.birth_date.addDays(week_index * 7)
        return date_value.toString("yyyy-MM-dd")

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
