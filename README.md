# Desktop Lyric

This project is 100% vibe coding,also README :)

A modern, transparent desktop overlay that displays synchronized lyrics for your currently playing music. Compatible with Apple Music, Spotify, and other Windows media players.

## Features

*   **Synchronized Lyrics**: Automatically fetches and displays time-synced lyrics (LRC) for the current song.
*   **Modern UI**: High-quality, anti-aliased text rendering with customizable outline and transparency.
*   **Media Integration**: Works with any player that supports Windows System Media Transport Controls (SMTC).
    *   **Smart Priority**: Automatically prioritizes the application that is currently *playing* music (e.g., switches from Apple Music to YouTube seamlessly).
*   **Customization**:
    *   **Fonts & Colors**: Choose any system font, size, and text color.
    *   **Positioning**: Drag and drop freely, or use presets (Top/Bottom Center).
    *   **Compact Mode**: Adjustable window height to save screen space.
*   **Click-Through Mode**: Optional mode that lets mouse clicks pass through the lyrics to windows behind them.
*   **System Tray Control**: Minimize to tray; control settings even when click-through is active.

## Installation

1.  **Prerequisites**:
    *   Python 3.9 or higher.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Requires `winsdk`, `syncedlyrics`, `PyQt6`, `qasync`)*

## Usage

1.  Run the application:
    *   Double-click `run.bat` (Windows).
    *   Or run `python main.py`.
2.  Play music in your favorite app (Apple Music, Spotify, etc.).
3.  **Right-click** the lyrics to access the menu:
    *   **Settings**: Configure font, color, alignment, and lyrics provider.
    *   **Exit**: Close the application.

### Click-Through Mode
If you enable "Click-Through Mode" in settings:
*   The window will ignore all mouse events.
*   To access settings or exit, look for the **System Tray Icon** (small white square or icon) in your taskbar notification area. Click it to open Settings.

## Configuration

Settings are saved automatically to `config.json`.

*   **Lyrics Source**: Default is "Auto", but you can force a provider (NetEase, Musixmatch, Genius, etc.) if lyrics are missing.
*   **Window Lock**: Prevent accidental dragging without enabling full click-through.
*   **Alignment**: Snap the lyrics to the top or bottom of your screen for a clean look.

## Troubleshooting

*   **Lyrics not showing?** Check if your media player supports Windows Media Controls. Try changing the "Lyrics Source" in settings.
*   **Window disappeared?** Check if "Click-Through" is on. Use the System Tray icon to reset it.
*   **Sync issues?** The app automatically corrects sync using monotonic time filtering. If it drifts, pausing and playing usually resets the sync.
