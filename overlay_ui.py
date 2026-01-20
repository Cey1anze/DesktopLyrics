from PyQt6.QtWidgets import QMainWindow, QLabel, QMenu, QApplication, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QColor, QAction, QPainter, QPainterPath, QPen
from settings_ui import SettingsWindow
import platform

class OutlinedLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outline_color = QColor("black")
        self.text_color = QColor("white")
        self.outline_width = 4
        self.setContentsMargins(0, 0, 0, 0)

    def set_colors(self, text_color_hex):
        self.text_color = QColor(text_color_hex)
        # Determine outline color based on brightness? Or just default to black/semi-transparent black
        self.outline_color = QColor(0, 0, 0, 200) # Semi-transparent black
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        font = self.font()
        
        # Center text
        rect = self.rect()
        text = self.text()
        
        # Calculate text position to center it
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(text)
        
        # X position
        x = (rect.width() - text_width) / 2
        
        # Y position (baseline)
        # ascent is distance from baseline to top
        # height is line spacing
        # To center vertically: Top + (Height - FontHeight)/2 + Ascent
        # But simpler: Center of rect + (Ascent - Descent)/2
        y = (rect.height() + fm.ascent() - fm.descent()) / 2

        path.addText(x, y, font, text)

        # Draw outline
        pen = QPen(self.outline_color, self.outline_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Draw text
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.text_color)
        painter.drawPath(path)

class OverlayWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        
        self.setWindowTitle("Desktop Lyrics")
        
        # Window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False) # Controlled by config

        # Label
        self.label = OutlinedLabel("Waiting for music...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.label)
        
        # Animation Effect - Removed for stability
        # self.opacity_effect = QGraphicsOpacityEffect(self.label)
        # self.label.setGraphicsEffect(self.opacity_effect)
        
        # self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        # self.fade_anim.setDuration(300) # ms
        # self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Apply Config
        self.apply_config()
        self.config_manager.add_listener(self.on_config_changed)

        # Dragging state
        self.old_pos = None

    def apply_config(self):
        # Geometry
        height = self.config_manager.get("window_height")
        alignment = self.config_manager.get("alignment")
        
        screen = QApplication.primaryScreen().geometry()
        screen_w = screen.width()
        screen_h = screen.height()
        
        # Use full width or large percentage to prevent clipping
        width = int(screen_w * 0.9)

        x = self.config_manager.get("window_x")
        y = self.config_manager.get("window_y")
        
        if alignment == "Top Center":
            x = (screen_w - width) // 2
            y = int(screen_h * 0.1) # 10% from top
        elif alignment == "Bottom Center":
            x = (screen_w - width) // 2
            y = int(screen_h * 0.85) # 15% from bottom
        elif alignment == "Center":
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            
        self.setGeometry(x, y, width, height)
        
        # Font
        family = self.config_manager.get("font_family")
        size = self.config_manager.get("font_size")
        font = QFont(family, size)
        font.setBold(True)
        self.label.setFont(font)
        
        # Color
        self.label.set_colors(self.config_manager.get("text_color"))
        
        # Click Through
        self.set_click_through(self.config_manager.get("click_through"))

    def set_click_through(self, enabled):
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enabled)
        # For full click-through (to windows behind), on Windows we might need to toggle WS_EX_TRANSPARENT if Qt doesn't handle it fully with WA_TransparentForMouseEvents.
        # But WA_TransparentForMouseEvents usually works for forwarding events.

    def on_config_changed(self):
        self.apply_config()

    def update_text(self, text):
        if text:
            text = text.strip()
        if self.label.text() != text:
            self.label.setText(text)
            self.label.update() # Force repaint
            
    # def animate_text_change(self, new_text): ...

    # Mouse Events for Dragging & Context Menu
    def mousePressEvent(self, event):
        if self.config_manager.get("click_through"):
            return # Should be handled by WA_TransparentForMouseEvents but just in case
            
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.config_manager.get("locked"):
                self.old_pos = event.globalPosition().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.old_pos and not self.config_manager.get("locked"):
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.old_pos:
            self.old_pos = None
            # Save position
            self.config_manager.set("window_x", self.x())
            self.config_manager.set("window_y", self.y())
            # Switch to Custom alignment if moved manually
            if self.config_manager.get("alignment") != "Custom":
                self.config_manager.set("alignment", "Custom")

    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_action)
        
        menu.exec(pos)

    def open_settings(self):
        self.settings_window = SettingsWindow(self, self.config_manager)
        self.settings_window.show()

    def closeEvent(self, event):
        # Ensure clean exit if needed
        super().closeEvent(event)
