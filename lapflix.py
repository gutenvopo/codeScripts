"""
LAPFLIX - a local Windows media manager for movies and TV shows.

Architecture:
- MediaScanner handles filesystem scanning and sorting.
- WatchHistoryManager owns the JSON history file.
- VLCLauncher opens media in VLC and reports friendly errors.
- LapflixApp builds the customtkinter interface and coordinates user actions.

Watch history is stored as JSON at:
C:\\Users\\kirwa\\Documents\\lapflix_watch_history.json

JSON is used for version 1 because it is easy to inspect, edit, back up, and
expand before the history grows enough to justify a database.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Any, Callable

try:
    import customtkinter as ctk
except ImportError as exc:
    raise SystemExit(
        "LAPFLIX requires customtkinter.\n\n"
        "Install the required packages with:\n"
        "pip install customtkinter pillow"
    ) from exc

try:
    from PIL import Image
except ImportError:
    Image = None


APP_NAME = "LAPFLIX"
MEDIA_ROOT = Path(r"C:\Users\kirwa\Documents")
MOVIES_DIR = MEDIA_ROOT / "movies"
SHOWS_DIR = MEDIA_ROOT / "shows"
LOGO_PATH = Path(r"C:\Users\kirwa\Documents\coding\codeScripts\lapflix_logo_edit3.png")
VLC_PATH = Path(r"C:\Program Files\VideoLAN\VLC\vlc.exe")
HISTORY_PATH = MEDIA_ROOT / "lapflix_watch_history.json"

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v", ".flv", ".webm"}

COLORS = {
    "app_bg": "#0B111E",
    "sidebar": "#101827",
    "panel": "#111C2E",
    "panel_alt": "#162237",
    "card": "#17253B",
    "card_hover": "#1D3150",
    "border": "#263A5B",
    "text": "#F4F8FF",
    "muted": "#8FA4C4",
    "accent": "#208DFF",
    "accent_hover": "#3BA0FF",
    "play": "#22C55E",
    "play_hover": "#16A34A",
    "danger": "#FF647C",
}


@dataclass(frozen=True)
class MovieItem:
    name: str
    folder: Path
    video_count: int


@dataclass(frozen=True)
class ShowItem:
    name: str
    folder: Path
    season_count: int


@dataclass(frozen=True)
class SeasonItem:
    name: str
    folder: Path
    number: int | None


@dataclass(frozen=True)
class EpisodeItem:
    name: str
    path: Path


class MediaScanner:
    """Scans local movie and show folders without assuming perfect filenames."""

    def __init__(self, movies_dir: Path, shows_dir: Path) -> None:
        self.movies_dir = movies_dir
        self.shows_dir = shows_dir

    @staticmethod
    def is_video_file(path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS

    @staticmethod
    def natural_key(value: str) -> list[Any]:
        parts = re.split(r"(\d+)", value.casefold())
        return [int(part) if part.isdigit() else part for part in parts]

    @staticmethod
    def season_number(name: str) -> int | None:
        patterns = (
            r"^\s*season\s*0*(\d+)\s*$",
            r"^\s*s\s*0*(\d+)\s*$",
            r"^\s*series\s*0*(\d+)\s*$",
        )
        for pattern in patterns:
            match = re.match(pattern, name, flags=re.IGNORECASE)
            if match:
                return int(match.group(1))
        generic_match = re.search(r"(\d+)", name)
        return int(generic_match.group(1)) if generic_match else None

    def scan_movies(self) -> tuple[list[MovieItem], str | None]:
        if not self.movies_dir.exists():
            return [], f"Movies folder was not found: {self.movies_dir}"

        movies: list[MovieItem] = []
        for folder in sorted((p for p in self.movies_dir.iterdir() if p.is_dir()), key=lambda p: self.natural_key(p.name)):
            video_count = len(self.find_videos(folder))
            movies.append(MovieItem(folder.name, folder, video_count))
        return movies, None

    def scan_shows(self) -> tuple[list[ShowItem], str | None]:
        if not self.shows_dir.exists():
            return [], f"Shows folder was not found: {self.shows_dir}"

        shows: list[ShowItem] = []
        for folder in sorted((p for p in self.shows_dir.iterdir() if p.is_dir()), key=lambda p: self.natural_key(p.name)):
            seasons = self.get_seasons(folder)
            shows.append(ShowItem(folder.name, folder, len(seasons)))
        return shows, None

    def get_seasons(self, show_folder: Path) -> list[SeasonItem]:
        if not show_folder.exists():
            return []

        seasons: list[SeasonItem] = []
        for folder in (p for p in show_folder.iterdir() if p.is_dir()):
            number = self.season_number(folder.name)
            seasons.append(SeasonItem(folder.name, folder, number))

        return sorted(
            seasons,
            key=lambda season: (
                season.number is None,
                season.number if season.number is not None else 999999,
                self.natural_key(season.name),
            ),
        )

    def get_episodes(self, season_folder: Path) -> list[EpisodeItem]:
        if not season_folder.exists():
            return []

        episodes = [
            EpisodeItem(path.name, path)
            for path in season_folder.iterdir()
            if self.is_video_file(path)
        ]
        return sorted(episodes, key=lambda episode: self.natural_key(episode.name))

    def find_videos(self, folder: Path) -> list[Path]:
        if not folder.exists():
            return []

        videos = [path for path in folder.rglob("*") if self.is_video_file(path)]
        return sorted(videos, key=lambda path: self.natural_key(path.name))

    def find_main_movie_file(self, movie_folder: Path) -> Path | None:
        videos = self.find_videos(movie_folder)
        if not videos:
            return None
        return max(videos, key=lambda path: path.stat().st_size if path.exists() else 0)


class WatchHistoryManager:
    """Stores a readable JSON watch history and repairs bad/missing files."""

    def __init__(self, history_path: Path) -> None:
        self.history_path = history_path
        self.data = self._load_or_create()

    def _blank_history(self) -> dict[str, Any]:
        return {"version": 1, "last_watched": None, "items": []}

    def _load_or_create(self) -> dict[str, Any]:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_path.exists():
            data = self._blank_history()
            self._save(data)
            return data

        try:
            with self.history_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("History root is not an object.")
            data.setdefault("version", 1)
            data.setdefault("last_watched", None)
            data.setdefault("items", [])
            return data
        except (json.JSONDecodeError, OSError, ValueError):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.history_path.with_suffix(f".corrupted_{timestamp}.json")
            try:
                shutil.copy2(self.history_path, backup_path)
            except OSError:
                pass
            data = self._blank_history()
            self._save(data)
            return data

    def _save(self, data: dict[str, Any] | None = None) -> None:
        payload = data if data is not None else self.data
        with self.history_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)

    def record_opened(
        self,
        *,
        media_type: str,
        file_path: Path,
        movie_name: str | None = None,
        show_name: str | None = None,
        season_name: str | None = None,
        episode_filename: str | None = None,
    ) -> dict[str, Any]:
        # TODO: Prevent the watch history file from growing too large.
        # TODO: Create a UI option to reset all watch history.
        # TODO: Create a UI option to reset watch history per movie.
        # TODO: Create a UI option to reset watch history per show.
        # TODO: Move watch history into SQLite later if JSON becomes too large or complex.
        # TODO: Exact playback position requires deeper VLC integration or reading VLC playback state.
        entry = {
            "media_type": media_type,
            "movie_name": movie_name,
            "show_name": show_name,
            "season_name": season_name,
            "episode_filename": episode_filename,
            "file_path": str(file_path),
            "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.data["last_watched"] = entry
        self.data.setdefault("items", []).append(entry)
        self._save()
        return entry

    def get_last_watched(self) -> dict[str, Any] | None:
        entry = self.data.get("last_watched")
        return entry if isinstance(entry, dict) else None

    def find_last_for_movie(self, movie_name: str) -> dict[str, Any] | None:
        for entry in reversed(self.data.get("items", [])):
            if entry.get("media_type") == "movie" and entry.get("movie_name") == movie_name:
                return entry
        return None

    def find_last_for_show(self, show_name: str) -> dict[str, Any] | None:
        for entry in reversed(self.data.get("items", [])):
            if entry.get("media_type") == "show" and entry.get("show_name") == show_name:
                return entry
        return None


class VLCLauncher:
    """Launches files using the configured VLC executable only."""

    def __init__(self, vlc_path: Path) -> None:
        self.vlc_path = vlc_path

    def open(self, video_path: Path) -> bool:
        # TODO: Later search common VLC locations automatically when media is selected.
        # TODO: Later allow embedding VLC inside the app window instead of opening VLC separately.
        if not self.vlc_path.exists():
            messagebox.showerror(
                "VLC not found",
                f"VLC was not found at:\n{self.vlc_path}\n\n"
                "LAPFLIX only opens media with VLC. Please install VLC or update VLC_PATH in the code.",
            )
            return False

        if not video_path.exists():
            messagebox.showerror("File not found", f"This media file no longer exists:\n{video_path}")
            return False

        try:
            subprocess.Popen([str(self.vlc_path), str(video_path)])
            return True
        except OSError as exc:
            messagebox.showerror("Could not open VLC", f"VLC could not open this file:\n{video_path}\n\n{exc}")
            return False


class LapflixApp(ctk.CTk):
    """Modern customtkinter interface for LAPFLIX."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_NAME)
        self.geometry("1380x840")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["app_bg"])

        self.scanner = MediaScanner(MOVIES_DIR, SHOWS_DIR)
        self.history = WatchHistoryManager(HISTORY_PATH)
        self.vlc = VLCLauncher(VLC_PATH)

        self.current_section = "movies"
        self.current_items: list[MovieItem | ShowItem] = []
        self.selected_movie: MovieItem | None = None
        self.selected_show: ShowItem | None = None
        self.selected_season: SeasonItem | None = None
        self.selected_episode: EpisodeItem | None = None
        self.seasons_by_name: dict[str, SeasonItem] = {}
        self.logo_image: ctk.CTkImage | None = None

        self._build_layout()
        self.show_movies()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=270, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(7, weight=1)

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["app_bg"])
        self.content.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        self.info_panel = ctk.CTkFrame(
            self,
            width=300,
            corner_radius=18,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.info_panel.grid(row=0, column=2, sticky="nsew", padx=(0, 18), pady=18)
        self.info_panel.grid_propagate(False)

        self._build_sidebar()
        self._build_content()
        self._build_info_panel()

    def _build_sidebar(self) -> None:
        logo_loaded = False
        if LOGO_PATH.exists() and Image is not None:
            try:
                image = Image.open(LOGO_PATH)
                logo_width = 230
                logo_height = round(logo_width * image.height / image.width)
                self.logo_image = ctk.CTkImage(light_image=image, dark_image=image, size=(logo_width, logo_height))
                ctk.CTkLabel(self.sidebar, image=self.logo_image, text="").grid(row=0, column=0, pady=(24, 8), padx=20)
                logo_loaded = True
            except OSError:
                logo_loaded = False

        if not logo_loaded:
            ctk.CTkLabel(
                self.sidebar,
                text="LF",
                width=230,
                height=150,
                corner_radius=18,
                fg_color=COLORS["panel_alt"],
                text_color=COLORS["accent"],
                font=ctk.CTkFont(size=42, weight="bold"),
            ).grid(row=0, column=0, pady=(24, 8), padx=20)

        self.movies_button = self._nav_button("Movies", self.show_movies)
        self.movies_button.grid(row=1, column=0, padx=20, pady=(18, 12), sticky="ew")

        self.shows_button = self._nav_button("Shows", self.show_shows)
        self.shows_button.grid(row=2, column=0, padx=20, pady=(0, 12), sticky="ew")

        ctk.CTkLabel(
            self.sidebar,
            text="Local media from\nC:\\Users\\kirwa\\Documents",
            justify="left",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=12),
        ).grid(row=8, column=0, padx=22, pady=22, sticky="sw")

    def _nav_button(self, text: str, command: Callable[[], None]) -> ctk.CTkButton:
        return ctk.CTkButton(
            self.sidebar,
            text=text,
            command=command,
            height=46,
            corner_radius=14,
            anchor="w",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text"],
        )

    def _build_content(self) -> None:
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            header,
            text="Movies",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=30, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.back_button = ctk.CTkButton(
            header,
            text="Back",
            width=112,
            height=38,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.go_back,
        )
        self.back_button.grid(row=0, column=1, sticky="e")

        self.toolbar = ctk.CTkFrame(self.content, fg_color="transparent")
        self.toolbar.grid(row=1, column=0, sticky="ew", pady=(18, 14))
        self.toolbar.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.apply_search_filter())
        self.search_entry = ctk.CTkEntry(
            self.toolbar,
            textvariable=self.search_var,
            placeholder_text="Search current list...",
            height=44,
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["panel"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted"],
        )
        self.search_entry.grid(row=0, column=0, sticky="ew")

        self.season_menu = ctk.CTkOptionMenu(
            self.toolbar,
            values=["No seasons"],
            command=self.on_season_selected,
            width=320,
            height=44,
            corner_radius=14,
            fg_color=COLORS["panel"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["panel_alt"],
            dropdown_hover_color=COLORS["card_hover"],
            text_color=COLORS["text"],
        )
        self.season_menu.grid(row=0, column=1, sticky="e", padx=(14, 0))
        self.season_menu.grid_remove()

        self.list_frame = ctk.CTkScrollableFrame(
            self.content,
            corner_radius=18,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.list_frame.grid(row=2, column=0, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.content,
            text="",
            anchor="w",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
        )
        self.status_label.grid(row=3, column=0, sticky="ew", pady=(12, 0))

    def _build_info_panel(self) -> None:
        self.info_panel.grid_columnconfigure(0, weight=1)
        self.info_panel.grid_rowconfigure(0, weight=1)
        self.info_panel.grid_rowconfigure(1, weight=1)

        self.details_top_panel = ctk.CTkFrame(
            self.info_panel,
            corner_radius=16,
            fg_color=COLORS["panel_alt"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.details_top_panel.grid(row=0, column=0, sticky="nsew", padx=18, pady=(18, 9))
        self.details_top_panel.grid_columnconfigure(0, weight=1)

        self.folder_history_panel = ctk.CTkFrame(
            self.info_panel,
            corner_radius=16,
            fg_color=COLORS["panel_alt"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.folder_history_panel.grid(row=1, column=0, sticky="nsew", padx=18, pady=(9, 18))
        self.folder_history_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.details_top_panel,
            text="Details",
            anchor="w",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 12))

        self.selected_info_label = ctk.CTkLabel(
            self.details_top_panel,
            text="Select a movie or show.",
            justify="left",
            anchor="nw",
            wraplength=220,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=16),
        )
        self.selected_info_label.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 18))

        ctk.CTkLabel(
            self.folder_history_panel,
            text="Last Watched In This Folder",
            anchor="w",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold"),
            wraplength=210,
            justify="left",
        ).grid(row=0, column=0, sticky="ew", padx=26, pady=(18, 12))

        self.folder_history_label = ctk.CTkLabel(
            self.folder_history_panel,
            text="Select a folder to see its last watched item.",
            justify="left",
            anchor="nw",
            wraplength=210,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
        )
        self.folder_history_label.grid(row=1, column=0, sticky="ew", padx=26, pady=(0, 18))

        self.continue_button = ctk.CTkButton(
            self.folder_history_panel,
            text="Continue Watching",
            height=44,
            corner_radius=14,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.continue_watching,
        )
        self.continue_button.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))

        self.update_history_panel()

    def set_nav_state(self, section: str) -> None:
        selected = COLORS["accent"]
        default = "transparent"
        self.movies_button.configure(fg_color=selected if section == "movies" else default)
        self.shows_button.configure(fg_color=selected if section == "shows" else default)

    def show_movies(self) -> None:
        self.current_section = "movies"
        self.selected_movie = None
        self.selected_show = None
        self.selected_season = None
        self.selected_episode = None
        self.season_menu.grid_remove()
        self.set_nav_state("movies")
        self.title_label.configure(text="Movies")
        self.search_var.set("")
        self.refresh_current()

    def show_shows(self) -> None:
        self.current_section = "shows"
        self.selected_movie = None
        self.selected_show = None
        self.selected_season = None
        self.selected_episode = None
        self.season_menu.grid_remove()
        self.set_nav_state("shows")
        self.title_label.configure(text="Shows")
        self.search_var.set("")
        self.refresh_current()

    def go_back(self) -> None:
        if self.current_section == "shows" and self.selected_show:
            self.selected_show = None
            self.selected_season = None
            self.selected_episode = None
            self.season_menu.grid_remove()
            self.search_var.set("")
            self.refresh_current()
            return

        if self.current_section == "movies" and self.selected_movie:
            self.selected_movie = None
            self.update_selected_info()
            return

        self.refresh_current()

    def refresh_current(self) -> None:
        if self.current_section == "movies":
            items, error = self.scanner.scan_movies()
        else:
            items, error = self.scanner.scan_shows()

        self.current_items = items
        self.render_items(items)
        self.update_status(len(items), error)
        self.update_selected_info()
        self.update_history_panel()

    def apply_search_filter(self) -> None:
        query = self.search_var.get().strip().casefold()
        if not query:
            self.render_items(self.current_items)
            self.update_status(len(self.current_items), None)
            return

        filtered = [item for item in self.current_items if query in item.name.casefold()]
        self.render_items(filtered)
        self.update_status(len(filtered), None)

    def clear_list(self) -> None:
        for widget in self.list_frame.winfo_children():
            widget.destroy()

    def render_items(self, items: list[MovieItem | ShowItem]) -> None:
        self.clear_list()
        if not items:
            self._empty_message("No items found.")
            return

        for index, item in enumerate(items):
            if isinstance(item, MovieItem):
                subtitle = f"{item.video_count} video file{'s' if item.video_count != 1 else ''}"
                command = lambda movie=item: self.on_movie_clicked(movie)
                play_command = lambda movie=item: self.play_movie(movie)
                icon_text = "MOV"
            else:
                subtitle = f"{item.season_count} season{'s' if item.season_count != 1 else ''}"
                command = lambda show=item: self.on_show_clicked(show)
                play_command = None
                icon_text = "TV"
            self._item_card(index, icon_text, item.name, subtitle, command, play_command)

    def render_episodes(self, episodes: list[EpisodeItem]) -> None:
        self.clear_list()
        if not episodes:
            self._empty_message("No episodes found.")
            self.update_status(0, None)
            return

        for index, episode in enumerate(episodes):
            command = lambda item=episode: self.on_episode_clicked(item)
            play_command = lambda item=episode: self.play_episode(item)
            self._item_card(index, "EP", episode.name, str(episode.path), command, play_command)
        self.update_status(len(episodes), None)

    def _bind_click(self, widget: ctk.CTkBaseClass, command: Callable[[], None]) -> None:
        widget.bind("<Button-1>", lambda _event: command())
        for child in widget.winfo_children():
            self._bind_click(child, command)

    def _item_card(
        self,
        row: int,
        icon_text: str,
        title: str,
        subtitle: str,
        command: Callable[[], None],
        play_command: Callable[[], None] | None = None,
    ) -> None:
        card = ctk.CTkFrame(
            self.list_frame,
            height=74,
            corner_radius=14,
            fg_color=COLORS["card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=row, column=0, sticky="ew", padx=12, pady=(12 if row == 0 else 6, 6))
        card.grid_columnconfigure(1, weight=1)
        card.grid_propagate(False)

        icon = ctk.CTkLabel(
            card,
            text=icon_text,
            width=48,
            height=48,
            corner_radius=12,
            fg_color=COLORS["panel_alt"],
            text_color=COLORS["accent"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        icon.grid(row=0, column=0, padx=(14, 12), pady=13)

        text_box = ctk.CTkFrame(card, fg_color="transparent")
        text_box.grid(row=0, column=1, sticky="ew", pady=10, padx=(0, 14))
        text_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            text_box,
            text=title,
            anchor="w",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            text_box,
            text=subtitle,
            anchor="w",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="ew", pady=(3, 0))
        self._bind_click(card, command)

        if play_command:
            ctk.CTkButton(
                text_box,
                text="Play",
                width=62,
                height=26,
                corner_radius=9,
                fg_color=COLORS["play"],
                hover_color=COLORS["play_hover"],
                text_color="#FFFFFF",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=play_command,
            ).grid(row=1, column=1, sticky="e", padx=(12, 0), pady=(1, 0))

    def _empty_message(self, text: str) -> None:
        ctk.CTkLabel(
            self.list_frame,
            text=text,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=15),
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=30)

    def update_status(self, count: int, error: str | None) -> None:
        if error:
            self.status_label.configure(text=error, text_color=COLORS["danger"])
        else:
            label = "movie folders" if self.current_section == "movies" else "shows"
            if self.selected_show and self.selected_season:
                label = "episodes"
            self.status_label.configure(text=f"{count} {label} found", text_color=COLORS["muted"])

    def on_movie_clicked(self, movie: MovieItem) -> None:
        self.selected_movie = movie
        self.selected_show = None
        self.selected_season = None
        self.selected_episode = None
        self.season_menu.grid_remove()
        self.update_selected_info()

    def play_movie(self, movie: MovieItem) -> None:
        self.on_movie_clicked(movie)
        video_path = self.scanner.find_main_movie_file(movie.folder)
        if video_path is None:
            messagebox.showinfo("No video found", f"No supported video file was found inside:\n{movie.folder}")
            return

        if self.vlc.open(video_path):
            self.history.record_opened(media_type="movie", movie_name=movie.name, file_path=video_path)
            self.update_history_panel()
            self.update_selected_info()

    def on_show_clicked(self, show: ShowItem) -> None:
        self.selected_movie = None
        self.selected_show = show
        self.selected_season = None
        self.selected_episode = None
        seasons = self.scanner.get_seasons(show.folder)
        self.seasons_by_name = {season.name: season for season in seasons}
        self.update_selected_info()

        if not seasons:
            self.season_menu.grid_remove()
            self.clear_list()
            self._empty_message("No seasons found.")
            self.update_status(0, None)
            return

        values = [season.name for season in seasons]
        self.season_menu.configure(values=values)
        self.season_menu.set(values[0])
        self.season_menu.grid(row=0, column=1, sticky="e", padx=(14, 0))
        self.on_season_selected(values[0])

    def on_season_selected(self, season_name: str) -> None:
        season = self.seasons_by_name.get(season_name)
        if season is None:
            return

        self.selected_season = season
        self.selected_episode = None
        episodes = self.scanner.get_episodes(season.folder)
        self.render_episodes(episodes)
        self.update_selected_info()

    def on_episode_clicked(self, episode: EpisodeItem) -> None:
        if not self.selected_show or not self.selected_season:
            return
        self.selected_episode = episode
        self.update_selected_info()

    def play_episode(self, episode: EpisodeItem) -> None:
        self.on_episode_clicked(episode)
        if not self.selected_show or not self.selected_season:
            return
        if self.vlc.open(episode.path):
            self.history.record_opened(
                media_type="show",
                show_name=self.selected_show.name,
                season_name=self.selected_season.name,
                episode_filename=episode.name,
                file_path=episode.path,
            )
            self.update_history_panel()
            self.update_selected_info()

    def update_selected_info(self) -> None:
        if self.selected_movie:
            self.selected_info_label.configure(text=self.selected_movie.name, font=ctk.CTkFont(size=24, weight="bold"))
            self.update_folder_history_panel(self.history.find_last_for_movie(self.selected_movie.name))
            return

        if self.selected_show:
            self.selected_info_label.configure(text=self.selected_show.name, font=ctk.CTkFont(size=24, weight="bold"))
            self.update_folder_history_panel(self.history.find_last_for_show(self.selected_show.name))
            return

        self.selected_info_label.configure(text="Select a movie or show.", font=ctk.CTkFont(size=16))
        self.update_folder_history_panel(None)

    def update_folder_history_panel(self, last: dict[str, Any] | None) -> None:
        if not last:
            self.folder_history_label.configure(text="No watch history in this folder yet.")
            return

        if last.get("media_type") == "movie":
            item = last.get("movie_name") or "Unknown movie"
        else:
            season = last.get("season_name") or "Unknown season"
            episode = last.get("episode_filename") or "Unknown episode"
            item = f"{season}\n{episode}"

        self.folder_history_label.configure(
            text=(
                f"Last item watched:\n{item}\n\n"
                f"Last watched:\n{last.get('opened_at', 'Unknown date')}"
            )
        )

    def update_history_panel(self) -> None:
        last = self.history.get_last_watched()
        if not last:
            self.continue_button.configure(state="disabled", fg_color=COLORS["border"])
            return

        self.continue_button.configure(state="normal", fg_color=COLORS["accent"])

    def continue_watching(self) -> None:
        last = self.history.get_last_watched()
        if not last:
            messagebox.showinfo("Nothing to continue", "No media has been watched yet.")
            return

        file_path = Path(last.get("file_path", ""))
        if self.vlc.open(file_path):
            if last.get("media_type") == "movie":
                self.history.record_opened(
                    media_type="movie",
                    movie_name=last.get("movie_name"),
                    file_path=file_path,
                )
            else:
                self.history.record_opened(
                    media_type="show",
                    show_name=last.get("show_name"),
                    season_name=last.get("season_name"),
                    episode_filename=last.get("episode_filename"),
                    file_path=file_path,
                )
            self.update_history_panel()
            self.update_selected_info()


def show_splash_then_open(app: LapflixApp) -> None:
    splash = ctk.CTkToplevel(app)
    splash.overrideredirect(True)
    splash.configure(fg_color=COLORS["app_bg"])
    splash.attributes("-topmost", True)

    splash_width = 420
    splash_height = 480
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - splash_width) // 2
    y = (screen_height - splash_height) // 2
    splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")

    splash.grid_columnconfigure(0, weight=1)
    splash.grid_rowconfigure(0, weight=1)

    if LOGO_PATH.exists() and Image is not None:
        try:
            image = Image.open(LOGO_PATH)
            logo_width = 320
            logo_height = round(logo_width * image.height / image.width)
            splash.logo_image = ctk.CTkImage(light_image=image, dark_image=image, size=(logo_width, logo_height))
            ctk.CTkLabel(splash, image=splash.logo_image, text="").grid(row=0, column=0)
        except OSError:
            pass

    def open_main_window() -> None:
        splash.destroy()
        app.deiconify()
        app.lift()
        app.focus_force()

    splash.after(1500, open_main_window)


def main() -> None:
    app = LapflixApp()
    app.withdraw()
    show_splash_then_open(app)
    app.mainloop()


if __name__ == "__main__":
    main()
