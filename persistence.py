import json
import os

from PySide6.QtCore import QDate, QTime


class PersistenceMixin:
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
