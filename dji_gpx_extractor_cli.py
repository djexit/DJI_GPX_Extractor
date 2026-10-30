# DJI MP4 -> GPX
# Copyright (c) 2026 Adam Kucia
# Author: Adam Kucia
# ManniAT: Added support for batch use

import sys
import json
import os
import queue
import re
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import Tk, StringVar, DoubleVar, filedialog, messagebox, Menu, Toplevel
from tkinter import ttk
from xml.sax.saxutils import escape


APP_NAME = "DJI GPX Extractor"
APP_VERSION = "0.8"


def get_config_path():
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else (Path.home() / "AppData" / "Roaming")
    cfg_dir = base / "DJI_MP4_to_GPX"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "config.json"


CONFIG_PATH = get_config_path()

def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).resolve().parent
    return str(base_path / relative_path)


LANGUAGES = {
    "en": "English",
    "pl": "Polski",
    "de": "Deutsch",
    "uk": "Українська",
}

T = {
    "en": {
        "app_name": "DJI GPX Extractor",
        "menu_file": "File",
        "menu_language": "Language",
        "menu_help": "Help",
        "menu_select_exiftool": "Select ExifTool...",
        "menu_select_video": "Select MP4/MOV...",
        "menu_convert": "Convert",
        "menu_exit": "Exit",
        "menu_exiftool_download": "Download ExifTool",
        "menu_about": "About",
        "convert_box": "Convert DJI MP4/MOV to GPX",
        "exiftool": "ExifTool.exe",
        "video_file": "MP4/MOV file",
        "output_file": "Save GPX as",
        "point_interval": "Point interval [s]",
        "choose": "Browse...",
        "select": "Select...",
        "change": "Change...",
        "convert": "Convert",
        "visual_box": "Visualize generated GPX",
        "visual_hint": "After conversion you can open the GPX file in one of these tools:",
        "download_exiftool": "Download ExifTool",
        "close": "Close",
        "status_initial": "Select ExifTool on first use, then choose an MP4/MOV file.",
        "copyright": "Copyright © 2026 Adam Kucia",
        "author_site": "adamk.pl",
        "open_author_site": "Open adamk.pl",
        "title_exiftool": "Select exiftool.exe",
        "title_video": "Select DJI MP4/MOV file",
        "title_output": "Where to save GPX?",
        "warn_exiftool": "First select exiftool.exe. The path will be saved.",
        "err_exiftool": "No valid exiftool.exe selected.",
        "err_video": "Select a valid MP4/MOV file.",
        "err_output": "Select where to save GPX.",
        "err_interval": "Point interval must be a number > 0.",
        "err_open_url": "Cannot open link:",
        "duration_detected": "Detected video duration: {seconds:.1f} s",
        "duration_unknown": "Video duration not detected; showing activity instead of percentage.",
        "status_start": "Starting...",
        "status_exiftool": "Starting ExifTool...",
        "status_reading": "Reading telemetry: {percent:.1f}% | records: {records}",
        "status_reading_count": "Reading telemetry... records: {records}",
        "status_building": "Building GPX points...",
        "status_saving": "Saving GPX...",
        "status_error": "Error.",
        "status_done": "Done.",
        "err_run_exiftool": "Cannot run ExifTool:",
        "err_exiftool_failed": "ExifTool finished with an error.",
        "err_no_gps": "No GPS points found in ExifTool data.",
        "err_save_gpx": "Cannot save GPX:",
        "done_msg": "Done.\nSaved {points} points to:\n{output}",
        "about": "DJI GPX Extractor\nVersion 0.8\nCopyright © 2026 Adam Kucia\n\nConverts DJI timed metadata from MP4/MOV to GPX using ExifTool.",
    },
    "pl": {
        "app_name": "DJI GPX Extractor",
        "menu_file": "Plik",
        "menu_language": "Język",
        "menu_help": "Pomoc",
        "menu_select_exiftool": "Wskaż ExifTool...",
        "menu_select_video": "Wybierz MP4/MOV...",
        "menu_convert": "Konwertuj",
        "menu_exit": "Zamknij",
        "menu_exiftool_download": "Pobierz ExifTool",
        "menu_about": "O programie",
        "convert_box": "Konwersja DJI MP4/MOV do GPX",
        "exiftool": "ExifTool.exe",
        "video_file": "Plik MP4/MOV",
        "output_file": "Zapisz GPX jako",
        "point_interval": "Interwał punktów [s]",
        "choose": "Wskaż...",
        "select": "Wybierz...",
        "change": "Zmień...",
        "convert": "Konwertuj",
        "visual_box": "Wizualizacja wygenerowanego GPX",
        "visual_hint": "Po konwersji możesz otworzyć plik GPX w jednym z poniższych narzędzi:",
        "download_exiftool": "Pobierz ExifTool",
        "close": "Zamknij",
        "status_initial": "Wskaż ExifTool przy pierwszym użyciu, potem wybierz plik MP4/MOV.",
        "copyright": "Copyright © 2026 Adam Kucia",
        "author_site": "adamk.pl",
        "open_author_site": "Open adamk.pl",
        "title_exiftool": "Wskaż exiftool.exe",
        "title_video": "Wybierz plik DJI MP4/MOV",
        "title_output": "Gdzie zapisać GPX?",
        "warn_exiftool": "Najpierw wskaż plik exiftool.exe. Ścieżka zostanie zapamiętana.",
        "err_exiftool": "Nie wskazano poprawnego pliku exiftool.exe.",
        "err_video": "Wskaż poprawny plik MP4/MOV.",
        "err_output": "Wskaż miejsce zapisu GPX.",
        "err_interval": "Interwał punktów musi być liczbą > 0.",
        "err_open_url": "Nie można otworzyć linku:",
        "duration_detected": "Wykryto czas filmu: {seconds:.1f} s",
        "duration_unknown": "Nie wykryto czasu filmu, pokazuję aktywność zamiast procentów.",
        "status_start": "Start...",
        "status_exiftool": "Uruchamiam ExifTool...",
        "status_reading": "Czytam telemetrię: {percent:.1f}% | rekordy: {records}",
        "status_reading_count": "Czytam telemetrię... rekordy: {records}",
        "status_building": "Buduję punkty GPX...",
        "status_saving": "Zapisuję GPX...",
        "status_error": "Błąd.",
        "status_done": "Gotowe.",
        "err_run_exiftool": "Nie można uruchomić ExifTool:",
        "err_exiftool_failed": "ExifTool zakończył się błędem.",
        "err_no_gps": "Nie znaleziono punktów GPS w danych ExifTool.",
        "err_save_gpx": "Nie można zapisać GPX:",
        "done_msg": "Gotowe.\nZapisano {points} punktów do:\n{output}",
        "about": "DJI GPX Extractor\nWersja 0.8\nCopyright © 2026 Adam Kucia\n\nKonwertuje metadane DJI z MP4/MOV do GPX używając ExifTool.",
    },
    "de": {
        "app_name": "DJI GPX Extractor",
        "menu_file": "Datei",
        "menu_language": "Sprache",
        "menu_help": "Hilfe",
        "menu_select_exiftool": "ExifTool auswählen...",
        "menu_select_video": "MP4/MOV auswählen...",
        "menu_convert": "Konvertieren",
        "menu_exit": "Beenden",
        "menu_exiftool_download": "ExifTool herunterladen",
        "menu_about": "Über",
        "convert_box": "DJI MP4/MOV zu GPX konvertieren",
        "exiftool": "ExifTool.exe",
        "video_file": "MP4/MOV-Datei",
        "output_file": "GPX speichern als",
        "point_interval": "Punktintervall [s]",
        "choose": "Durchsuchen...",
        "select": "Auswählen...",
        "change": "Ändern...",
        "convert": "Konvertieren",
        "visual_box": "Erzeugte GPX-Datei visualisieren",
        "visual_hint": "Nach der Konvertierung kannst du die GPX-Datei mit einem dieser Tools öffnen:",
        "download_exiftool": "ExifTool herunterladen",
        "close": "Schließen",
        "status_initial": "Beim ersten Start ExifTool auswählen, danach eine MP4/MOV-Datei wählen.",
        "copyright": "Copyright © 2026 Adam Kucia",
        "author_site": "adamk.pl",
        "open_author_site": "Open adamk.pl",
        "title_exiftool": "exiftool.exe auswählen",
        "title_video": "DJI MP4/MOV-Datei auswählen",
        "title_output": "GPX speichern unter",
        "warn_exiftool": "Bitte zuerst exiftool.exe auswählen. Der Pfad wird gespeichert.",
        "err_exiftool": "Keine gültige exiftool.exe ausgewählt.",
        "err_video": "Bitte eine gültige MP4/MOV-Datei auswählen.",
        "err_output": "Bitte Speicherort für GPX auswählen.",
        "err_interval": "Das Punktintervall muss eine Zahl > 0 sein.",
        "err_open_url": "Link kann nicht geöffnet werden:",
        "duration_detected": "Videodauer erkannt: {seconds:.1f} s",
        "duration_unknown": "Videodauer nicht erkannt; Aktivitätsanzeige statt Prozentanzeige.",
        "status_start": "Start...",
        "status_exiftool": "ExifTool wird gestartet...",
        "status_reading": "Telemetrie wird gelesen: {percent:.1f}% | Datensätze: {records}",
        "status_reading_count": "Telemetrie wird gelesen... Datensätze: {records}",
        "status_building": "GPX-Punkte werden erstellt...",
        "status_saving": "GPX wird gespeichert...",
        "status_error": "Fehler.",
        "status_done": "Fertig.",
        "err_run_exiftool": "ExifTool kann nicht gestartet werden:",
        "err_exiftool_failed": "ExifTool wurde mit einem Fehler beendet.",
        "err_no_gps": "Keine GPS-Punkte in den ExifTool-Daten gefunden.",
        "err_save_gpx": "GPX kann nicht gespeichert werden:",
        "done_msg": "Fertig.\n{points} Punkte gespeichert in:\n{output}",
        "about": "DJI GPX Extractor\nVersion 0.8\nCopyright © 2026 Adam Kucia\n\nKonvertiert DJI-Metadaten aus MP4/MOV mit ExifTool nach GPX.",
    },
    "uk": {
        "app_name": "DJI GPX Extractor",
        "menu_file": "Файл",
        "menu_language": "Мова",
        "menu_help": "Довідка",
        "menu_select_exiftool": "Вибрати ExifTool...",
        "menu_select_video": "Вибрати MP4/MOV...",
        "menu_convert": "Конвертувати",
        "menu_exit": "Вийти",
        "menu_exiftool_download": "Завантажити ExifTool",
        "menu_about": "Про програму",
        "convert_box": "Конвертація DJI MP4/MOV у GPX",
        "exiftool": "ExifTool.exe",
        "video_file": "Файл MP4/MOV",
        "output_file": "Зберегти GPX як",
        "point_interval": "Інтервал точок [с]",
        "choose": "Огляд...",
        "select": "Вибрати...",
        "change": "Змінити...",
        "convert": "Конвертувати",
        "visual_box": "Візуалізація створеного GPX",
        "visual_hint": "Після конвертації можна відкрити GPX-файл в одному з цих інструментів:",
        "download_exiftool": "Завантажити ExifTool",
        "close": "Закрити",
        "status_initial": "Під час першого запуску виберіть ExifTool, потім виберіть файл MP4/MOV.",
        "copyright": "Copyright © 2026 Adam Kucia",
        "author_site": "adamk.pl",
        "open_author_site": "Open adamk.pl",
        "title_exiftool": "Вибрати exiftool.exe",
        "title_video": "Вибрати файл DJI MP4/MOV",
        "title_output": "Куди зберегти GPX?",
        "warn_exiftool": "Спочатку виберіть exiftool.exe. Шлях буде збережено.",
        "err_exiftool": "Не вибрано коректний файл exiftool.exe.",
        "err_video": "Виберіть коректний файл MP4/MOV.",
        "err_output": "Виберіть місце збереження GPX.",
        "err_interval": "Інтервал точок має бути числом > 0.",
        "err_open_url": "Не вдалося відкрити посилання:",
        "duration_detected": "Виявлено тривалість відео: {seconds:.1f} с",
        "duration_unknown": "Тривалість відео не виявлено; показується індикатор активності.",
        "status_start": "Старт...",
        "status_exiftool": "Запуск ExifTool...",
        "status_reading": "Зчитування телеметрії: {percent:.1f}% | записів: {records}",
        "status_reading_count": "Зчитування телеметрії... записів: {records}",
        "status_building": "Створення точок GPX...",
        "status_saving": "Збереження GPX...",
        "status_error": "Помилка.",
        "status_done": "Готово.",
        "err_run_exiftool": "Не вдалося запустити ExifTool:",
        "err_exiftool_failed": "ExifTool завершився з помилкою.",
        "err_no_gps": "GPS-точки не знайдено в даних ExifTool.",
        "err_save_gpx": "Не вдалося зберегти GPX:",
        "done_msg": "Готово.\nЗбережено {points} точок у:\n{output}",
        "about": "DJI GPX Extractor\nВерсія 0.8\nCopyright © 2026 Adam Kucia\n\nКонвертує DJI timed metadata з MP4/MOV у GPX за допомогою ExifTool.",
    },
}

line_re = re.compile(r'^\s*(?:\d+\s+)?\[(Doc\d+)\]\s+(.+?)\s+:\s+(.*?)\s*$')


def load_config():
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_config(data):
    try:
        CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def parse_sample_time(value):
    value = value.strip()
    parts = value.split(":")
    try:
        if len(parts) == 3:
            h, m, s = parts
            return float(h) * 3600 + float(m) * 60 + float(s)
        if len(parts) == 2:
            m, s = parts
            return float(m) * 60 + float(s)
        return float(value)
    except Exception:
        return None


def parse_duration(value):
    value = value.strip()

    t = parse_sample_time(value)
    if t is not None:
        return t

    total = 0.0

    m = re.search(r"(\d+(?:\.\d+)?)\s*h", value, re.I)
    if m:
        total += float(m.group(1)) * 3600

    m = re.search(r"(\d+(?:\.\d+)?)\s*m(?:in)?", value, re.I)
    if m:
        total += float(m.group(1)) * 60

    m = re.search(r"(\d+(?:\.\d+)?)\s*s(?:ec)?", value, re.I)
    if m:
        total += float(m.group(1))

    return total if total > 0 else None


def dms_to_decimal(value):
    m = re.search(r'([0-9.]+)\s+deg\s+([0-9.]+)\'\s+([0-9.]+)"\s+([NSEW])', value)
    if not m:
        try:
            return float(value)
        except Exception:
            return None

    deg, minutes, seconds, hemi = m.groups()
    dec = float(deg) + float(minutes) / 60.0 + float(seconds) / 3600.0

    if hemi in ("S", "W"):
        dec *= -1

    return dec


def normalize_time(value):
    value = value.strip()
    m = re.match(r"(\d{4}):(\d{2}):(\d{2})\s+(.+)", value)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}"
    return value


def get_duration_seconds(exiftool, input_file):
    cmd = [
        exiftool,
        "-api", "LargeFileSupport=1",
        "-s3",
        "-Duration",
        input_file,
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=30,
        )
    except Exception:
        return None

    if proc.returncode != 0:
        return None

    for line in proc.stdout.splitlines():
        duration = parse_duration(line)
        if duration:
            return duration

    return None


def convert_mp4_to_gpx(exiftool, input_file, output_file, step_seconds, q, lang):
    tr = lambda key: T.get(lang, T["en"]).get(key, T["en"].get(key, key))

    duration = get_duration_seconds(exiftool, input_file)

    if duration:
        q.put(("duration", duration))
    else:
        q.put(("indeterminate", None))

    cmd = [
        exiftool,
        "-ee",
        "-G3",
        "-api", "LargeFileSupport=1",
        input_file,
    ]

    q.put(("status", tr("status_exiftool")))

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            bufsize=1,
        )
    except Exception as exc:
        q.put(("error", f"{tr('err_run_exiftool')}\n{exc}"))
        return

    records = {}
    sample_count = 0
    last_progress_time = -1.0

    assert proc.stdout is not None

    for line in proc.stdout:
        m = line_re.match(line)
        if not m:
            continue

        doc, key, value = m.groups()
        key = key.strip()
        value = value.strip()

        doc_data = records.setdefault(doc, {})
        doc_data[key] = value

        if key == "Sample Time":
            sample_count += 1
            t = parse_sample_time(value)

            if t is not None and duration and duration > 0 and t > last_progress_time:
                last_progress_time = t
                percent = max(0.0, min(100.0, (t / duration) * 100.0))
                q.put(("progress", percent))
                q.put(("status", tr("status_reading").format(percent=percent, records=sample_count)))
            elif sample_count % 250 == 0:
                q.put(("status", tr("status_reading_count").format(records=sample_count)))

    stderr = proc.stderr.read() if proc.stderr else ""
    ret = proc.wait()

    if ret != 0:
        q.put(("error", stderr.strip() or tr("err_exiftool_failed")))
        return

    q.put(("status", tr("status_building")))

    points = []

    for data in records.values():
        sample_time = data.get("Sample Time")
        lat_raw = data.get("GPS Latitude")
        lon_raw = data.get("GPS Longitude")

        if not sample_time or not lat_raw or not lon_raw:
            continue

        t = parse_sample_time(sample_time)
        lat = dms_to_decimal(lat_raw)
        lon = dms_to_decimal(lon_raw)

        if t is None or lat is None or lon is None:
            continue

        ele = data.get("Absolute Altitude") or data.get("Relative Altitude") or ""
        gps_time = data.get("GPS Date/Time", "")

        try:
            ele = float(ele)
        except Exception:
            ele = None

        points.append({
            "sample_time": t,
            "lat": lat,
            "lon": lon,
            "ele": ele,
            "gps_time": normalize_time(gps_time) if gps_time else "",
            "yaw": data.get("Drone Yaw", ""),
            "pitch": data.get("Drone Pitch", ""),
            "roll": data.get("Drone Roll", ""),
        })

    points.sort(key=lambda x: x["sample_time"])

    filtered = []
    last_t = -999999.0

    for p in points:
        if p["sample_time"] >= last_t + step_seconds:
            filtered.append(p)
            last_t = p["sample_time"]

    if not filtered:
        q.put(("error", tr("err_no_gps")))
        return

    q.put(("status", tr("status_saving")))

    try:
        with open(output_file, "w", encoding="utf-8", newline="\n") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<gpx version="1.1" creator="DJI MP4 to GPX GUI" ')
            f.write('xmlns="http://www.topografix.com/GPX/1/1" ')
            f.write('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
            f.write('xsi:schemaLocation="http://www.topografix.com/GPX/1/1 ')
            f.write('http://www.topografix.com/GPX/1/1/gpx.xsd">\n')
            f.write("  <trk>\n")
            f.write(f"    <name>{escape(Path(input_file).name)}</name>\n")
            f.write("    <trkseg>\n")

            for p in filtered:
                f.write(f'      <trkpt lat="{p["lat"]:.8f}" lon="{p["lon"]:.8f}">\n')

                if p["ele"] is not None:
                    f.write(f'        <ele>{p["ele"]:.3f}</ele>\n')

                if p["gps_time"]:
                    f.write(f'        <time>{escape(p["gps_time"])}</time>\n')

                desc = (
                    f'sample_time={p["sample_time"]:.3f}; '
                    f'yaw={p["yaw"]}; pitch={p["pitch"]}; roll={p["roll"]}'
                )
                f.write(f'        <desc>{escape(desc)}</desc>\n')
                f.write("      </trkpt>\n")

            f.write("    </trkseg>\n")
            f.write("  </trk>\n")
            f.write("</gpx>\n")

    except Exception as exc:
        q.put(("error", f"{tr('err_save_gpx')}\n{exc}"))
        return

    q.put(("progress", 100.0))
    q.put(("done", tr("done_msg").format(points=len(filtered), output=output_file)))


class App:
    def __init__(self, root):
        self.root = root
        self.root.geometry("900x500")
        self.root.minsize(860, 460)

        cfg = load_config()

        self.lang = cfg.get("language", "en")
        if self.lang not in LANGUAGES:
            self.lang = "en"

        self.root.title(f"{self.tr('app_name')} v{APP_VERSION}")
        try:
            self.root.iconbitmap(resource_path("ikona.ico"))
        except Exception:
            pass

        self.exiftool_var = StringVar(value=cfg.get("exiftool", ""))
        self.input_var = StringVar(value="")
        self.output_var = StringVar(value="")
        self.step_var = DoubleVar(value=float(cfg.get("step_seconds", 1.0)))

        self.q = queue.Queue()
        self.worker = None
        self.indeterminate = False

        self.build_ui()
        self.root.after(100, self.poll_queue)

    def tr(self, key):
        return T.get(self.lang, T["en"]).get(key, T["en"].get(key, key))

    def build_menu(self):
        self.menubar = Menu(self.root)

        file_menu = Menu(self.menubar, tearoff=0)
        file_menu.add_command(label=self.tr("menu_select_exiftool"), command=self.browse_exiftool)
        file_menu.add_command(label=self.tr("menu_select_video"), command=self.browse_input)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("menu_convert"), command=self.start)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("menu_exit"), command=self.root.destroy)
        self.menubar.add_cascade(label=self.tr("menu_file"), menu=file_menu)

        language_menu = Menu(self.menubar, tearoff=0)
        for code, name in LANGUAGES.items():
            language_menu.add_command(label=name, command=lambda c=code: self.set_language(c))
        self.menubar.add_cascade(label=self.tr("menu_language"), menu=language_menu)

        help_menu = Menu(self.menubar, tearoff=0)
        help_menu.add_command(label=self.tr("menu_exiftool_download"), command=lambda: self.open_url("https://exiftool.org/"))
        help_menu.add_separator()
        help_menu.add_command(label=self.tr("menu_about"), command=self.show_about)
        self.menubar.add_cascade(label=self.tr("menu_help"), menu=help_menu)

        self.root.config(menu=self.menubar)

    def build_ui(self):
        self.build_menu()

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        convert_box = ttk.LabelFrame(main, text=self.tr("convert_box"), padding=10)
        convert_box.pack(fill="x", expand=False)
        convert_box.columnconfigure(1, weight=1)

        ttk.Label(convert_box, text=self.tr("exiftool")).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(convert_box, textvariable=self.exiftool_var).grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        exiftool_buttons = ttk.Frame(convert_box)
        exiftool_buttons.grid(row=0, column=2, sticky="ew", padx=8, pady=6)

        ttk.Button(exiftool_buttons, text=self.tr("choose"), command=self.browse_exiftool).pack(side="left")
        ttk.Button(
            exiftool_buttons,
            text=self.tr("download_exiftool"),
            command=lambda: self.open_url("https://exiftool.org/")
        ).pack(side="left", padx=(6, 0))

        ttk.Label(convert_box, text=self.tr("video_file")).grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(convert_box, textvariable=self.input_var).grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        ttk.Button(convert_box, text=self.tr("select"), command=self.browse_input).grid(row=1, column=2, sticky="ew", padx=8, pady=6)

        ttk.Label(convert_box, text=self.tr("output_file")).grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(convert_box, textvariable=self.output_var).grid(row=2, column=1, sticky="ew", padx=8, pady=6)
        ttk.Button(convert_box, text=self.tr("change"), command=self.browse_output).grid(row=2, column=2, sticky="ew", padx=8, pady=6)

        options_row = ttk.Frame(convert_box)
        options_row.grid(row=3, column=0, columnspan=3, sticky="ew", padx=8, pady=(6, 2))

        ttk.Label(options_row, text=self.tr("point_interval")).pack(side="left")
        ttk.Spinbox(options_row, from_=0.1, to=10.0, increment=0.1, textvariable=self.step_var, width=8).pack(side="left", padx=(8, 18))

        self.start_btn = ttk.Button(options_row, text=self.tr("convert"), command=self.start)
        self.start_btn.pack(side="right")

        self.progress = ttk.Progressbar(convert_box, mode="determinate", maximum=100)
        self.progress.grid(row=4, column=0, columnspan=3, sticky="ew", padx=8, pady=(10, 4))

        self.status_var = StringVar(value=self.tr("status_initial"))
        ttk.Label(convert_box, textvariable=self.status_var).grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=(2, 6))

        visual_box = ttk.LabelFrame(main, text=self.tr("visual_box"), padding=10)
        visual_box.pack(fill="x", expand=False, pady=(14, 0))

        ttk.Label(visual_box, text=self.tr("visual_hint")).pack(anchor="w", padx=8, pady=(0, 8))

        links_row = ttk.Frame(visual_box)
        links_row.pack(anchor="w", padx=2)

        ttk.Button(
            links_row,
            text="DJI Telemetry Overlay SRT Viewer",
            command=lambda: self.open_url("https://djitelemetryoverlay.com/srt-viewer/")
        ).pack(side="left", padx=6, pady=4)

        ttk.Button(
            links_row,
            text="GPS Visualizer",
            command=lambda: self.open_url("https://www.gpsvisualizer.com/")
        ).pack(side="left", padx=6, pady=4)

        ttk.Button(
            links_row,
            text="Google Earth Web",
            command=lambda: self.open_url("https://earth.google.com/web/")
        ).pack(side="left", padx=6, pady=4)

        footer = ttk.Frame(main)
        footer.pack(side="bottom", fill="x", pady=(12, 0))

        author_label = ttk.Label(
            footer,
            text=f"{self.tr('copyright')} | v{APP_VERSION} | adamk.pl",
            anchor="center",
            foreground="blue",
            cursor="hand2"
        )
        author_label.pack(side="top", fill="x")
        author_label.bind("<Button-1>", lambda _e: self.open_url("http://adamk.pl"))

        bottom_buttons = ttk.Frame(footer)
        bottom_buttons.pack(side="right", pady=(6, 0))

        ttk.Button(bottom_buttons, text=self.tr("close"), command=self.root.destroy).pack(side="right")

    def set_language(self, lang):
        if lang not in LANGUAGES:
            return

        self.lang = lang
        self.persist_config()
        self.rebuild_ui()

    def rebuild_ui(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.root.config(menu="")
        self.root.title(f"{self.tr('app_name')} v{APP_VERSION}")
        try:
            self.root.iconbitmap(resource_path("ikona.ico"))
        except Exception:
            pass
        self.build_ui()

    def show_about(self):
        dlg = Toplevel(self.root)
        dlg.title(self.tr("menu_about"))
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        try:
            dlg.iconbitmap(resource_path("ikona.ico"))
        except Exception:
            pass

        frame = ttk.Frame(dlg, padding=16)
        frame.pack(fill="both", expand=True)

        about_lines = self.tr("about").splitlines()
        main_text = "\n".join(line for line in about_lines if not line.startswith("Copyright"))
        ttk.Label(frame, text=main_text, justify="left").pack(anchor="w", pady=(0, 10))

        copyright_link = ttk.Label(
            frame,
            text=f"{self.tr('copyright')} | adamk.pl",
            foreground="blue",
            cursor="hand2"
        )
        copyright_link.pack(anchor="w")
        copyright_link.bind("<Button-1>", lambda _e: self.open_url("http://adamk.pl"))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(16, 0))

        ttk.Button(buttons, text="OK", command=dlg.destroy).pack(side="right")

        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def browse_exiftool(self):
        path = filedialog.askopenfilename(
            title=self.tr("title_exiftool"),
            filetypes=[("ExifTool", "exiftool.exe"), ("EXE", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.exiftool_var.set(path)
            self.persist_config()

    def browse_input(self):
        path = filedialog.askopenfilename(
            title=self.tr("title_video"),
            filetypes=[("DJI video", "*.mp4 *.mov *.MP4 *.MOV"), ("All files", "*.*")]
        )
        if not path:
            return

        self.input_var.set(path)

        default_output = str(Path(path).with_suffix(".gpx"))
        out = filedialog.asksaveasfilename(
            title=self.tr("title_output"),
            initialdir=str(Path(path).parent),
            initialfile=Path(default_output).name,
            defaultextension=".gpx",
            filetypes=[("GPX", "*.gpx"), ("All files", "*.*")]
        )

        if out:
            self.output_var.set(out)
        else:
            self.output_var.set(default_output)

    def browse_output(self):
        input_path = self.input_var.get().strip()
        if input_path:
            default = Path(input_path).with_suffix(".gpx")
            initialdir = str(default.parent)
            initialfile = default.name
        else:
            initialdir = str(Path.cwd())
            initialfile = "output.gpx"

        out = filedialog.asksaveasfilename(
            title=self.tr("title_output"),
            initialdir=initialdir,
            initialfile=initialfile,
            defaultextension=".gpx",
            filetypes=[("GPX", "*.gpx"), ("All files", "*.*")]
        )

        if out:
            self.output_var.set(out)

    def open_url(self, url):
        try:
            webbrowser.open(url)
        except Exception as exc:
            messagebox.showerror(self.tr("app_name"), f"{self.tr('err_open_url')}\n{exc}")

    def persist_config(self):
        save_config({
            "exiftool": self.exiftool_var.get().strip(),
            "step_seconds": self.step_var.get(),
            "language": self.lang,
        })

    def set_busy(self, busy):
        state = "disabled" if busy else "normal"
        self.start_btn.configure(state=state)

    def start(self):
        exiftool = self.exiftool_var.get().strip()
        input_file = self.input_var.get().strip()
        output_file = self.output_var.get().strip()

        if not exiftool or not Path(exiftool).exists():
            messagebox.showwarning(self.tr("app_name"), self.tr("warn_exiftool"))
            self.browse_exiftool()
            exiftool = self.exiftool_var.get().strip()

            if not exiftool or not Path(exiftool).exists():
                messagebox.showerror(self.tr("app_name"), self.tr("err_exiftool"))
                return

        if not input_file or not Path(input_file).exists():
            messagebox.showerror(self.tr("app_name"), self.tr("err_video"))
            return

        if not output_file:
            messagebox.showerror(self.tr("app_name"), self.tr("err_output"))
            return

        try:
            step = float(self.step_var.get())
            if step <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror(self.tr("app_name"), self.tr("err_interval"))
            return

        self.persist_config()

        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress["value"] = 0
        self.status_var.set(self.tr("status_start"))
        self.set_busy(True)

        self.worker = threading.Thread(
            target=convert_mp4_to_gpx,
            args=(exiftool, input_file, output_file, step, self.q, self.lang),
            daemon=True,
        )
        self.worker.start()

    def poll_queue(self):
        try:
            while True:
                kind, value = self.q.get_nowait()

                if kind == "duration":
                    self.indeterminate = False
                    self.progress.stop()
                    self.progress.configure(mode="determinate")
                    self.progress["value"] = 0
                    self.status_var.set(self.tr("duration_detected").format(seconds=value))

                elif kind == "indeterminate":
                    self.indeterminate = True
                    self.progress.configure(mode="indeterminate")
                    self.progress.start(12)
                    self.status_var.set(self.tr("duration_unknown"))

                elif kind == "progress":
                    if not self.indeterminate:
                        self.progress["value"] = value

                elif kind == "status":
                    self.status_var.set(value)

                elif kind == "error":
                    self.progress.stop()
                    self.set_busy(False)
                    self.status_var.set(self.tr("status_error"))
                    messagebox.showerror(self.tr("app_name"), value)

                elif kind == "done":
                    self.progress.stop()
                    self.set_busy(False)
                    self.status_var.set(self.tr("status_done"))
                    messagebox.showinfo(self.tr("app_name"), value)

        except queue.Empty:
            pass

        self.root.after(100, self.poll_queue)

def main():
    # If no arguments are passed at all -> Start standard GUI Mode immediately
    if len(sys.argv) == 1:
        root = Tk()
        App(root)
        root.mainloop()
        return

    # If arguments are passed, handle CLI / Batch Mode
    import argparse
    from pathlib import Path
    import queue

    # Dynamically detect the current executable or script name (e.g., ext.py or my_tool.exe)
    current_prog = Path(sys.argv[0]).name

    # Determine the correct prefix for the help menu based on file extension
    if current_prog.lower().endswith('.py'):
        cmd_prefix = f"python {current_prog}"
    else:
        cmd_prefix = current_prog

    # Custom usage text explaining both GUI and CLI usage modes cleanly
    custom_usage = (
        f"\n  GUI Mode:  {cmd_prefix} (Or double-click the file to run without arguments)\n"
        f"  CLI Mode:  {cmd_prefix} -s SOURCE [-d DEST] [-i INTERVAL]"
    )

    parser = argparse.ArgumentParser(
        description="DJI GPX Batch Extractor - Converts DJI timed metadata from MP4/MOV to GPX.",
        usage=custom_usage,
        prog=current_prog
    )
    parser.add_argument("-s", "--source", required=True, help="Path to video file, directory, or wildcard pattern (e.g. C:\\Folder\\*.mp4)")
    parser.add_argument("-d", "--dest", help="Optional destination directory for the generated GPX files")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Point interval in seconds (Default: 1.0)")
    
    # If invalid single arguments are provided, show help explicitly before parsing fails
    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(0)
    
    # Load existing configuration to retrieve the saved ExifTool path from GUI
    cfg = load_config()
    exiftool_path = cfg.get("exiftool", "exiftool.exe")
    
    if not os.path.exists(exiftool_path):
        print(f"Error: exiftool.exe not found at: {exiftool_path}")
        print("Please run the application once via GUI to set up your ExifTool path.")
        sys.exit(1)

    source_path = Path(args.source)
    
    # Check if wildcards (* or ?) are used, or if it is a direct directory/file path
    if "*" in args.source or "?" in args.source:
        search_dir = Path(source_path.parent)
        search_pattern = source_path.name
        files = list(set(search_dir.glob(search_pattern)))
    elif source_path.is_dir():
        files = []
        for ext in ("*.mp4", "*.mov", "*.MP4", "*.MOV"):
            files.extend(source_path.glob(ext))
        files = list(set(files))
    elif source_path.is_file():
        files = [source_path]
    else:
        print(f"Error: Source path '{args.source}' does not exist or is invalid.")
        sys.exit(1)

    if not files:
        print("No matching DJI video files found.")
        sys.exit(0)

    print(f"Found {len(files)} DJI video(s). Starting batch conversion...")
    q = queue.Queue()

    for f in files:
        input_file = str(f)
        
        # Determine destination directory
        if args.dest:
            dest_dir = Path(args.dest)
            dest_dir.mkdir(parents=True, exist_ok=True)
            output_file = str(dest_dir / f.with_suffix(".gpx").name)
        else:
            output_file = str(f.with_suffix(".gpx"))

        print(f"Processing: {f.name}")
        convert_mp4_to_gpx(exiftool_path, input_file, output_file, args.interval, q, "de")
        
        while not q.empty():
            kind, value = q.get()
            if kind == "done":
                print(f"Success: {f.name}")
            elif kind == "error":
                print(f"Error processing {f.name}: {value}")
                
    print("Batch processing completed.")
    sys.exit(0)



if __name__ == "__main__":
    main()
