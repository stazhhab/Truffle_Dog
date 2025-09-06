#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import csv
import threading
import sys
import subprocess
import math

# Versuch, den optionalen Datepicker aus tkcalendar zu importieren.
try:
    from tkcalendar import DateEntry  # type: ignore
    HAVE_DATEENTRY = True
except ImportError:
    HAVE_DATEENTRY = False

"""
TruffleDog – Archivsuche (UI präzisiert, Funktion unverändert)
==============================================================

- Durchsucht XML-Dateien nach Personen anhand von Geburtsdatum, Name oder beidem.
- **Funktional unverändert** (Namespace, Filterlogik, Threads, Export).
- **Logo oben rechts**, **Suchhund unten** (läuft während der Suche).
- Farben bleiben wie gehabt (bg='light blue').
"""

# Namespace für die XML-Dateien
NS = {'ns': 'http://www.unisys.com/polis/staatsarchiv/geschaeftsliste'}

# Bildpfade (deine absoluten Pfade zuerst, dann Fallback in Skriptordner)
DEFAULT_LOGO_PATH = r"C:\Users\BZZ1391\Bingo\Truffle_Dog\Logo.png"
DEFAULT_DOG_PATH  = r"C:\Users\BZZ1391\Bingo\Truffle_Dog\Suchhund.png"


def debug(msg: str) -> None:
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


class ArchiveSearchApp(tk.Tk):
    """GUI-Applikation zur Suche nach Personen in XML-Archiven."""

    def __init__(self) -> None:
        super().__init__()
        # Fenstereigenschaften
        self.title("TruffleDog – Archivsuche")
        # Feinjusierte Startgröße; sauberes Resize-Verhalten
        self.geometry("1000x680")
        self.minsize(900, 600)

        debug("Initialisiere Applikation ...")

        # Variablen für Threads und Ergebnisse
        self.search_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.results: list[tuple[str, str, str]] = []

        # Animation-Zustand
        self.anim_running = False
        self.anim_job: str | None = None
        self.anim_dx = 6
        self.dog_item: int | None = None
        self.dog_x = 40.0
        self.dog_img: tk.PhotoImage | None = None
        self.dog_img_raw: tk.PhotoImage | None = None
        self.logo_img: tk.PhotoImage | None = None

        # UI-Aufbau
        self._create_widgets()
        self._style_widgets()
        self._load_images()

        # Event für Fensterschließen
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ------------------------------------------------------------------
    # UI-Aufbau
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        """Erstellt alle Widgets und ordnet sie in Frames an."""
        # Oberer Frame (Suchkriterien und Aktionen)
        top_frame = tk.Frame(self, bg='light blue')
        top_frame.pack(fill='x', padx=10, pady=10)

        # Grid-Konfiguration für saubere Ausrichtung
        for col in range(4):
            top_frame.grid_columnconfigure(col, weight=1 if col in (1, 2) else 0)

        # Titel (links) + Logo (rechts)
        title_label = tk.Label(
            top_frame,
            text="TruffleDog – Archive Search",
            font=('Helvetica', 16, 'bold'),
            bg='light blue'
        )
        title_label.grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 6))

        # Logo-Platzhalter rechts (wird nach Bild-Load gesetzt)
        self.logo_label = tk.Label(top_frame, bg='light blue')
        self.logo_label.grid(row=0, column=3, sticky='e', pady=(0, 6))

        # Suchtyp (Geburtsdatum, Name oder beides)
        search_label = tk.Label(top_frame, text="Suchart:", font=('Helvetica', 12), bg='light blue')
        search_label.grid(row=1, column=0, sticky='e', pady=4)

        self.search_var = tk.StringVar(value="birth")
        rb_birth = tk.Radiobutton(top_frame, text="Geburtsdatum", variable=self.search_var, value="birth", bg='light blue')
        rb_name  = tk.Radiobutton(top_frame, text="Name",          variable=self.search_var, value="name",  bg='light blue')
        rb_both  = tk.Radiobutton(top_frame, text="Beides",        variable=self.search_var, value="both",  bg='light blue')
        rb_birth.grid(row=1, column=1, sticky='w', padx=(4, 0))
        rb_name.grid (row=1, column=2, sticky='w', padx=(4, 0))
        rb_both.grid (row=1, column=3, sticky='w', padx=(4, 0))

        # Datumseingabe
        date_label = tk.Label(top_frame, text="Geburtsdatum (TT-MM-JJJJ):", font=('Helvetica', 12), bg='light blue')
        date_label.grid(row=2, column=0, sticky='e', pady=4)

        if HAVE_DATEENTRY:
            self.date_entry = DateEntry(
                top_frame,
                date_pattern='dd-MM-yyyy',
                locale='de_DE',
                firstweekday='monday',
            )
            self.date_entry.grid(row=2, column=1, columnspan=3, sticky='w')
            self.day_combobox = None  # type: ignore
            self.month_combobox = None  # type: ignore
            self.year_combobox = None  # type: ignore
        else:
            self.day_combobox   = ttk.Combobox(top_frame, values=[f"{i:02d}" for i in range(1, 32)], width=3)
            self.month_combobox = ttk.Combobox(top_frame, values=[f"{i:02d}" for i in range(1, 13)], width=3)
            current_year = datetime.datetime.now().year
            self.year_combobox  = ttk.Combobox(top_frame, values=[str(i) for i in range(1900, current_year + 1)], width=5)
            self.day_combobox.grid(row=2, column=1, sticky='w')
            self.month_combobox.grid(row=2, column=2, sticky='w')
            self.year_combobox.grid(row=2, column=3, sticky='w')

        # Nameingabe
        name_label = tk.Label(top_frame, text="Name:", font=('Helvetica', 12), bg='light blue')
        name_label.grid(row=3, column=0, sticky='e', pady=4)
        self.name_entry = tk.Entry(top_frame)
        self.name_entry.grid(row=3, column=1, columnspan=3, sticky='we')

        # Verzeichniswahl (unveränderte Funktion)
        directory_label = tk.Label(top_frame, text="Suchverzeichnis:", font=('Helvetica', 12), bg='light blue')
        directory_label.grid(row=4, column=0, sticky='e', pady=4)
        self.directory_entry = tk.Entry(top_frame)
        self.directory_entry.grid(row=4, column=1, columnspan=2, sticky='we')
        dir_button = tk.Button(top_frame, text="Verzeichnis wählen", command=self._choose_directory)
        dir_button.grid(row=4, column=3, sticky='w')

        # Aktionsbuttons
        btns = tk.Frame(top_frame, bg='light blue')
        btns.grid(row=5, column=0, columnspan=4, pady=(8, 2), sticky='we')
        btns.grid_columnconfigure(0, weight=1)
        btns.grid_columnconfigure(1, weight=1)
        btns.grid_columnconfigure(2, weight=1)
        btns.grid_columnconfigure(3, weight=1)

        clear_button  = tk.Button(btns, text="Löschen",     command=self._clear_results)
        search_button = tk.Button(btns, text="Suchen",      command=self._start_search)
        cancel_button = tk.Button(btns, text="Abbrechen",   command=self._cancel_search)
        export_button = tk.Button(btns, text="Exportieren", command=self._export_results)

        clear_button.grid (row=0, column=0, padx=4, sticky='we')
        search_button.grid(row=0, column=1, padx=4, sticky='we')
        cancel_button.grid(row=0, column=2, padx=4, sticky='we')
        export_button.grid(row=0, column=3, padx=4, sticky='we')

        # Fortschrittsbalken
        self.progress = ttk.Progressbar(top_frame, orient='horizontal', mode='determinate')
        self.progress.grid(row=6, column=0, columnspan=4, sticky='we', pady=(6, 0))

        # Unterer Frame für Ergebnisliste
        results_frame = tk.Frame(self, bg='light blue')
        results_frame.pack(fill='both', expand=True, padx=10, pady=(0, 6))
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        columns = ("Name", "Geburtsdatum", "Datei")
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Datei":
                self.tree.column(col, width=500, anchor='w')
            elif col == "Name":
                self.tree.column(col, width=180, anchor='w')
            else:
                self.tree.column(col, width=130, anchor='center')

        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        # Doppelklick zum Öffnen der ausgewählten Datei
        self.tree.bind("<Double-1>", self._open_selected_file)

        # Unterer Frame für Animation (Hund unten, volle Breite)
        bottom_frame = tk.Frame(self, bg='light blue')
        bottom_frame.pack(fill='x', padx=10, pady=(0, 10))
        # Canvas für Hund
        self.anim_canvas = tk.Canvas(bottom_frame, height=110, bg='light blue', highlightthickness=0)
        self.anim_canvas.pack(fill='x', expand=True)
        self.anim_canvas.bind("<Configure>", self._on_canvas_resize)

    def _style_widgets(self) -> None:
        """Anpassung einiger Stilparameter von Treeview."""
        style = ttk.Style()
        # Thema beibehalten; Schrift sauber setzen
        style.configure("Treeview", font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 11, 'bold'))

    # ------------------------------------------------------------------
    # Bilder laden (Logo oben rechts, Hund unten)
    # ------------------------------------------------------------------
    def _first_existing(self, *candidates: str) -> str | None:
        for p in candidates:
            if p and os.path.exists(p):
                return p
        return None

    def _load_images(self) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Logo: oben rechts
        logo_path = self._first_existing(DEFAULT_LOGO_PATH, os.path.join(script_dir, "Logo.png"))
        if logo_path:
            try:
                img = tk.PhotoImage(file=logo_path)
                # ggf. etwas verkleinern, damit es oben rechts sauber sitzt
                max_h = 60
                if img.height() > max_h:
                    factor = max(1, math.ceil(img.height() / max_h))
                    img = img.subsample(factor, factor)
                self.logo_img = img
                self.logo_label.configure(image=self.logo_img)
                debug(f"Logo geladen: {logo_path} ({img.width()}x{img.height()})")
            except Exception as e:
                debug(f"[WARN] Fehler beim Laden des Logos: {e}")
        else:
            debug("[INFO] Kein Logo gefunden (optional).")

        # Hund: unten (Animation)
        dog_path = self._first_existing(DEFAULT_DOG_PATH, os.path.join(script_dir, "Suchhund.png"))
        if dog_path:
            try:
                self.dog_img_raw = tk.PhotoImage(file=dog_path)
                self._prepare_dog_image()
                debug(f"Hund geladen: {dog_path} ({self.dog_img_raw.width()}x{self.dog_img_raw.height()})")
            except Exception as e:
                debug(f"[WARN] Fehler beim Laden des Hundebildes: {e}")
        else:
            debug("[INFO] Kein Suchhund-Bild gefunden – Animation deaktiviert.")

    # ------------------------------------------------------------------
    # Animation (Hund unten)
    # ------------------------------------------------------------------
    def _prepare_dog_image(self) -> None:
        if not self.dog_img_raw:
            return
        canvas_h = max(1, int(self.anim_canvas.winfo_height() or 110) - 10)
        factor = max(1, math.ceil(self.dog_img_raw.height() / canvas_h))
        self.dog_img = self.dog_img_raw.subsample(factor, factor)
        if self.dog_item is not None and self.dog_img:
            cy = self._canvas_center_y()
            self.anim_canvas.itemconfigure(self.dog_item, image=self.dog_img)
            self.anim_canvas.coords(self.dog_item, self.dog_x, cy)

    def _canvas_center_y(self) -> float:
        h = max(1, self.anim_canvas.winfo_height())
        return h / 2

    def _dog_bounds(self) -> tuple[float, float]:
        w = max(1, self.anim_canvas.winfo_width())
        dog_w = self.dog_img.width() if self.dog_img else 0
        pad = 12
        left = pad + dog_w / 2
        right = w - pad - dog_w / 2
        if right < left:
            right = left
        return left, right

    def _on_canvas_resize(self, _event: tk.Event) -> None:
        self._prepare_dog_image()
        if self.dog_item is not None and self.dog_img is not None:
            left, right = self._dog_bounds()
            self.dog_x = min(max(self.dog_x, left), right)
            self.anim_canvas.coords(self.dog_item, self.dog_x, self._canvas_center_y())

    def _start_animation(self) -> None:
        if not self.dog_img:
            return
        if self.anim_running:
            return
        self.anim_running = True
        if self.dog_item is None:
            cy = self._canvas_center_y()
            left, _ = self._dog_bounds()
            self.dog_x = left
            self.dog_item = self.anim_canvas.create_image(self.dog_x, cy, image=self.dog_img, anchor="center")
        debug("Animation START.")
        self._animate_step()

    def _animate_step(self) -> None:
        if not self.anim_running or not self.dog_item or not self.dog_img:
            return
        left, right = self._dog_bounds()
        self.dog_x += self.anim_dx
        if self.dog_x <= left or self.dog_x >= right:
            self.anim_dx *= -1
            self.dog_x = min(max(self.dog_x, left), right)
        self.anim_canvas.coords(self.dog_item, self.dog_x, self._canvas_center_y())
        self.anim_job = self.after(30, self._animate_step)

    def _stop_animation(self) -> None:
        if not self.anim_running:
            return
        self.anim_running = False
        if self.anim_job:
            try:
                self.after_cancel(self.anim_job)
            except Exception:
                pass
            self.anim_job = None
        debug("Animation STOP.")

    # ------------------------------------------------------------------
    # Benutzereingaben und Hilfsfunktionen
    # ------------------------------------------------------------------
    def _choose_directory(self) -> None:
        """Öffnet einen Dialog zur Verzeichniswahl und setzt den Pfad im Eingabefeld."""
        directory = filedialog.askdirectory()
        if directory:
            debug(f"Verzeichnis gewählt: {directory}")
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, directory)

    def _clear_results(self) -> None:
        """Entfernt alle Einträge aus der Ergebnisliste."""
        debug("Lösche Ergebnisse...")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results = []
        self.progress["value"] = 0

    def _cancel_search(self) -> None:
        """Bricht eine laufende Suche ab."""
        if self.search_thread and self.search_thread.is_alive():
            debug("Suche wird abgebrochen...")
            self.stop_event.set()
        else:
            debug("Keine aktive Suche zum Abbrechen.")

    def _validate_date(self) -> bool:
        """
        Validiert die Datumsangabe (unverändert).
        """
        if HAVE_DATEENTRY and getattr(self, 'date_entry', None) is not None:
            return True
        try:
            day = int(self.day_combobox.get())
            month = int(self.month_combobox.get())
            year = int(self.year_combobox.get())
            datetime.date(year, month, day)
            return True
        except Exception:
            messagebox.showerror("Ungültiges Datum", "Bitte geben Sie ein gültiges Datum ein.")
            return False

    # ------------------------------------------------------------------
    # Hauptsuche (unverändert – nur Animation gestartet/gestoppt)
    # ------------------------------------------------------------------
    def _start_search(self) -> None:
        """Startet die Suche in einem separaten Thread und initialisiert den Fortschrittsbalken."""
        if self.search_thread and self.search_thread.is_alive():
            messagebox.showwarning("Suche läuft", "Bitte warten Sie, bis die aktuelle Suche abgeschlossen ist oder brechen Sie sie ab.")
            return

        search_type = self.search_var.get()
        directory = self.directory_entry.get().strip()
        if not directory:
            messagebox.showwarning("Warnung", "Bitte wählen Sie ein Suchverzeichnis.")
            return

        # Datum validieren, falls benötigt
        date_str = ""
        if search_type in ("birth", "both"):
            if not self._validate_date():
                return
            if HAVE_DATEENTRY and getattr(self, 'date_entry', None) is not None:
                dt = self.date_entry.get_date()
                date_str = dt.strftime('%Y-%m-%d')
            else:
                day = self.day_combobox.get().strip().zfill(2)
                month = self.month_combobox.get().strip().zfill(2)
                year = self.year_combobox.get().strip()
                date_str = f"{year}-{month}-{day}"

        # Name abfragen, falls benötigt
        name_value = ""
        if search_type in ("name", "both"):
            name_value = self.name_entry.get().strip()
            if not name_value:
                messagebox.showwarning("Warnung", "Bitte geben Sie einen Namen ein.")
                return

        # Bisherige Ergebnisse löschen
        self._clear_results()
        self.stop_event.clear()

        # XML-Dateien sammeln (unverändert)
        xml_files: list[str] = []
        for root_dir, _, files in os.walk(directory):
            for f in files:
                if f.lower().endswith(".xml"):
                    xml_files.append(os.path.join(root_dir, f))
        if not xml_files:
            messagebox.showinfo("Information", "Keine XML-Dateien im angegebenen Verzeichnis gefunden.")
            return

        debug(f"Anzahl XML-Dateien zum Durchsuchen: {len(xml_files)}")

        # Fortschrittsbalken initialisieren
        self.progress["maximum"] = len(xml_files)
        self.progress["value"] = 0

        # Hund laufen lassen
        self._start_animation()

        # Suchthread starten
        self.search_thread = threading.Thread(
            target=self._run_search,
            args=(xml_files, search_type, date_str, name_value),
            daemon=True
        )
        self.search_thread.start()
        debug("Suchthread gestartet.")

    def _run_search(self, xml_files: list[str], search_type: str, date_str: str, name_value: str) -> None:
        """Durchsucht die XML-Dateien im Hintergrundthread und aktualisiert den Fortschritt."""
        debug(f"Starte Suche nach Suchart '{search_type}' ...")
        results_local: list[tuple[str, str, str]] = []
        for idx, file_path in enumerate(xml_files, start=1):
            if self.stop_event.is_set():
                debug("Suche wurde durch Benutzer abgebrochen.")
                break
            try:
                entries = self._search_in_xml(file_path, search_type, date_str, name_value)
                results_local.extend(entries)
            except Exception as e:
                debug(f"Fehler beim Verarbeiten von {file_path}: {e}")
            # Fortschritt aktualisieren
            self._update_progress(idx)
        # Ergebnisse an das UI übergeben
        self.after(0, lambda: self._on_search_complete(results_local))

    def _update_progress(self, value: int) -> None:
        """Aktualisiert den Fortschrittsbalken im Hauptthread."""
        self.after(0, lambda val=value: self.progress.configure(value=val))

    def _on_search_complete(self, results_local: list[tuple[str, str, str]]) -> None:
        """Wird aufgerufen, wenn die Suche abgeschlossen ist oder abgebrochen wurde."""
        if self.stop_event.is_set():
            messagebox.showinfo("Abgebrochen", "Die Suche wurde abgebrochen.")
        else:
            messagebox.showinfo("Fertig", f"Suche abgeschlossen. Gefundene Einträge: {len(results_local)}")
        self.results = results_local
        self._display_results(results_local)
        # Fortschrittsbalken zurücksetzen
        self.progress["value"] = 0
        self.search_thread = None

        # Hund anhalten
        self._stop_animation()

    # ------------------------------------------------------------------
    # XML-Analyse (unverändert)
    # ------------------------------------------------------------------
    @staticmethod
    def _search_in_xml(file_path: str, search_type: str, date_str: str, name_value: str) -> list[tuple[str, str, str]]:
        """Durchsucht eine einzelne XML-Datei nach passenden Personen."""
        found_entries: list[tuple[str, str, str]] = []
        try:
            tree = ET.parse(file_path)
        except ET.ParseError:
            debug(f"Fehler beim Parsen der Datei: {file_path}")
            return found_entries
        root = tree.getroot()
        for person in root.findall('.//ns:Person', NS):
            name_node = person.find('ns:Name', NS)
            birth_node = person.find('ns:Geburtsdatum', NS)
            person_name = name_node.text if name_node is not None else ""
            person_birth = birth_node.text if birth_node is not None else ""
            match = False
            if search_type == "birth":
                match = (person_birth == date_str)
            elif search_type == "name":
                match = name_value.lower() in person_name.lower()
            elif search_type == "both":
                match = (person_birth == date_str and name_value.lower() in person_name.lower())
            if match:
                found_entries.append((person_name or "Unbekannt", person_birth or "", file_path))
        return found_entries

    # ------------------------------------------------------------------
    # Ergebnisdarstellung und Export
    # ------------------------------------------------------------------
    def _display_results(self, results: list[tuple[str, str, str]]) -> None:
        debug("Ergebnisse anzeigen...")
        # Bestehende Zeilen entfernen
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Neue Zeilen einfügen
        for row in results:
            self.tree.insert("", "end", values=row)

    def _export_results(self) -> None:
        """Exportiert die aktuellen Ergebnisse als CSV."""
        if not self.results:
            messagebox.showinfo("Keine Daten", "Es gibt keine Ergebnisse zum Exportieren.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Dateien", "*.csv")])
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Name", "Geburtsdatum", "Datei"])
                for row in self.results:
                    writer.writerow(row)
            messagebox.showinfo("Exportiert", f"Ergebnisse erfolgreich exportiert nach:\n{file_path}")
            debug(f"Ergebnisse exportiert nach {file_path}")
        except Exception as exc:
            messagebox.showerror("Fehler", f"Fehler beim Exportieren der Datei: {exc}")

    def _open_selected_file(self, event: tk.Event) -> None:
        """Öffnet die ausgewählte Datei mit der systemeigenen Anwendung."""
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, 'values')
        if len(values) < 3:
            return
        file_path = values[2]
        if not os.path.exists(file_path):
            messagebox.showerror("Fehler", f"Datei existiert nicht: {file_path}")
            return
        debug(f"Öffne Datei: {file_path}")
        try:
            if sys.platform.startswith('darwin'):
                subprocess.Popen(['open', file_path])  # macOS
            elif os.name == 'nt':
                os.startfile(file_path)  # Windows
            elif os.name == 'posix':
                subprocess.Popen(['xdg-open', file_path])  # Linux
            else:
                messagebox.showinfo("Nicht unterstützt", "Das Öffnen der Datei wird auf diesem System nicht unterstützt.")
        except Exception as exc:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen der Datei: {exc}")

    # ------------------------------------------------------------------
    # Fensterverwaltung
    # ------------------------------------------------------------------
    def _on_closing(self) -> None:
        """Reagiert auf das Schließen des Fensters und fragt bei laufender Suche nach."""
        if self.search_thread and self.search_thread.is_alive():
            if not messagebox.askokcancel("Beenden", "Eine Suche läuft noch. Möchten Sie das Programm wirklich schließen?"):
                return
            # Laufende Suche abbrechen
            self.stop_event.set()
        self._stop_animation()
        self.destroy()


# Haupteinstiegspunkt
if __name__ == "__main__":
    app = ArchiveSearchApp()
    app.mainloop()
