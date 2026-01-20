import sys
import asyncio
import time
import threading # Still needed for sync lyrics fetching maybe? Or make it async.
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from qasync import QEventLoop, asyncSlot

from overlay_ui import OverlayWindow
from media_monitor import MediaMonitor
from lyrics_fetcher import LyricsFetcher
from config_manager import ConfigManager
from settings_ui import SettingsWindow

class DesktopLyricApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False) # Keep running for tray

        self.loop = QEventLoop(self.app)
        asyncio.set_event_loop(self.loop)

        self.config_manager = ConfigManager()
        self.ui = OverlayWindow(self.config_manager)
        self.fetcher = LyricsFetcher()
        
        self.current_lyrics = []
        self.current_song_key = None # (title, artist)
        self.last_info = None
        self.info_timestamp = 0
        self.last_monotonic_pos = 0 # Track last position to prevent jitter backwards

        # System Tray
        self.setup_tray()

        self.ui.show()

        # Start background tasks
        self.loop.create_task(self.run_monitor())
        self.loop.create_task(self.update_loop())

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app)
        # We need an icon. Since we don't have one, we can create a simple pixmap or use a standard icon if available.
        # Or just use the window icon if set.
        # For now, let's try to set a simple text icon or no icon (might not show on Windows).
        # Actually, PyQt requires an icon for the tray to show.
        # Let's create a simple colored pixmap.
        from PyQt6.QtGui import QPixmap, QColor
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("white"))
        self.tray_icon.setIcon(QIcon(pixmap))
        
        tray_menu = QMenu()
        
        settings_action = QAction("Settings", self.app)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("Exit", self.app)
        exit_action.triggered.connect(self.app.quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("Desktop Lyrics")
        self.tray_icon.show()

        # Connect click
        self.tray_icon.activated.connect(self.on_tray_click)

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_settings()

    def open_settings(self):
        self.settings_window = SettingsWindow(None, self.config_manager)
        self.settings_window.show()

    async def run_monitor(self):
        monitor = MediaMonitor()
        await monitor.initialize()
        while True:
            try:
                info = await monitor.get_media_info()
                if info:
                    self.last_info = info
                    # Fallback timestamp if last_updated is missing
                    if not info.get('last_updated'):
                        self.info_timestamp = time.time()
            except Exception as e:
                print(f"Monitor error: {e}")
            
            await asyncio.sleep(0.1) # Check more frequently

    async def update_loop(self):
        while True:
            self.update_ui()
            await asyncio.sleep(0.05) # UI refresh rate faster

    def update_ui(self):
        info = self.last_info
        
        if info:
            artist = info.get('artist')
            title = info.get('title')
            status = info.get('status') # 4=Playing, 5=Paused
            
            # Check song change
            song_key = (title, artist)
            if song_key != self.current_song_key:
                self.current_song_key = song_key
                self.current_lyrics = [] 
                self.last_monotonic_pos = 0
                self.ui.update_text(f"Fetching: {title} - {artist}")
                
                # Run fetch in executor to not block asyncio loop
                provider = self.config_manager.get("provider")
                self.loop.run_in_executor(None, self.fetch_lyrics_sync, artist, title, provider)
            
            # Calculate current position
            if status == 4: # Playing
                # Use last_updated from SMTC if available for better precision
                last_updated = info.get('last_updated')
                now = time.time()
                
                # Check for stale data (e.g. if music paused but status stuck, or drift)
                # If last_updated is too old (> 1 hour), might be stale.
                # But mostly, just calculate elapsed.
                
                if last_updated and last_updated > 0:
                    elapsed = now - last_updated
                else:
                    elapsed = now - self.info_timestamp
                
                # Cap elapsed time to avoid runaway timers if song ended but we didn't get update
                # Song duration + 5 seconds buffer
                duration = info.get('duration', 0)
                if duration > 0 and (info['position'] + elapsed) > (duration + 5):
                     # Maybe we missed the pause event?
                     # Don't clamp strictly, but maybe stop updating if it's absurdly long
                     pass
                
                raw_pos = info['position'] + elapsed
                
                # Apply monotonic filter to prevent jittering backwards
                # If the drop is small (< 1.0s), it's likely jitter, so we clamp to previous max.
                # If the drop is large, it's a user seek, so we accept it.
                if raw_pos < self.last_monotonic_pos:
                    if self.last_monotonic_pos - raw_pos < 1.0:
                        current_pos = self.last_monotonic_pos
                    else:
                        current_pos = raw_pos # Seek detected
                else:
                    # If we jumped forward significantly (e.g. 5s) without a seek event (unlikely but possible),
                    # we still accept it.
                    current_pos = raw_pos
                
                # Check if song looped (pos reset to near 0)
                if current_pos < 5.0 and self.last_monotonic_pos > 30.0:
                     self.last_monotonic_pos = current_pos # Reset filter for loop
                elif raw_pos < self.last_monotonic_pos:
                     pass # Already handled above by clamped assignment
                else:
                     self.last_monotonic_pos = max(self.last_monotonic_pos, current_pos)
            else:
                current_pos = info['position']
                self.last_monotonic_pos = current_pos

            # Find lyric line
            current_line = ""
            if self.current_lyrics:
                for t, text in self.current_lyrics:
                    if t <= current_pos:
                        current_line = text
                    else:
                        break
            
            # Debug position and line
            # print(f"Pos: {current_pos:.2f}, Line: {current_line}")

            # Fallback to Title - Artist if no lyrics found
            if not current_line:
                # If we have lyrics but waiting for intro
                if self.current_lyrics:
                     current_line = "..."
                # If we don't have lyrics yet (or failed)
                elif self.current_song_key:
                     # Check if we are still fetching? 
                     # We don't have a flag for that easily here without more state.
                     # But if it's been a while, we should show title.
                     # For now, let's just show title if we don't have lyrics.
                     # The "Fetching" message will be overwritten.
                     current_line = f"{title} - {artist}"
            
            if current_line:
                self.ui.update_text(current_line)

        else:
            self.ui.update_text("Waiting for music...")

    def fetch_lyrics_sync(self, artist, title, provider):
        try:
            lyrics = self.fetcher.get_lyrics(artist, title, provider)
            if lyrics:
                self.current_lyrics = lyrics
            else:
                self.current_lyrics = []
                print(f"No lyrics found for {title}")
        except Exception as e:
            print(f"Fetch error: {e}")

    def run(self):
        with self.loop:
            self.loop.run_forever()

if __name__ == "__main__":
    app = DesktopLyricApp()
    app.run()
