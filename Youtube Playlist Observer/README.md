# Youtube Playlist Observer

Youtube Playlist Observer is a small Tkinter desktop app for turning a YouTube playlist into a Markdown song list.

## What It Does

- Accepts a YouTube playlist URL.
- Lets you export all entries, individual positions, ranges, or mixed selections like `1, 4, 10-15`.
- Reads playlist metadata with `yt-dlp` without downloading videos.
- Supports optional YouTube cookies for private, age-restricted, or region-sensitive playlists.
- Saves the selected playlist entries as a Markdown `.md` file.
- Provides buttons to open the generated Markdown file or its folder after export.

## Files

- `ytube_playlist_song_list_gui_v1.00.py` - original v1.00 version.
- `ytube_playlist_song_list_gui_v2.00.py` - v2.00 version.
- `CHANGELOG.md` - release notes to update whenever a new version is created.

## Requirements

Install `yt-dlp` for the Python environment used to run the app:

```powershell
python -m pip install yt-dlp
```

Tkinter is also required. It is included with most standard Python installations on Windows.

## Running

From this folder, run the version you want:

```powershell
python .\ytube_playlist_song_list_gui_v2.00.py
```

## Release Process

When creating a new version:

1. Copy the latest script and update the filename version.
2. Update the version text inside the script.
3. Add a new entry at the top of `CHANGELOG.md`.
4. Keep older versions in this folder for reference.
