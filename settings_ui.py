from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QFontComboBox, 
    QSpinBox, QPushButton, QColorDialog, QCheckBox, 
    QLabel, QHBoxLayout, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

class SettingsWindow(QDialog):
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 450) # Increased height
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Font Family
        self.font_combo = QFontComboBox()
        current_font = self.config_manager.get("font_family")
        self.font_combo.setCurrentFont(QFont(current_font))
        self.font_combo.currentFontChanged.connect(self.on_font_change)
        form_layout.addRow("Font Family:", self.font_combo)

        # Font Size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 120)
        self.size_spin.setValue(self.config_manager.get("font_size"))
        self.size_spin.valueChanged.connect(self.on_size_change)
        form_layout.addRow("Font Size:", self.size_spin)

        # Text Color
        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self.choose_color)
        self.update_color_btn_style()
        form_layout.addRow("Text Color:", self.color_btn)

        # Provider
        self.provider_combo = QComboBox()
        # Based on syncedlyrics providers
        providers = ["Auto", "Musixmatch", "NetEase", "Lrclib", "Deezer", "Megalobiz", "Genius"]
        self.provider_combo.addItems(providers)
        current_provider = self.config_manager.get("provider")
        index = self.provider_combo.findText(current_provider)
        if index >= 0:
            self.provider_combo.setCurrentIndex(index)
        self.provider_combo.currentTextChanged.connect(self.on_provider_change)
        form_layout.addRow("Lyrics Source:", self.provider_combo)

        # Alignment
        self.align_combo = QComboBox()
        alignments = ["Custom", "Top Center", "Bottom Center", "Center"]
        self.align_combo.addItems(alignments)
        current_align = self.config_manager.get("alignment")
        index = self.align_combo.findText(current_align)
        if index >= 0:
            self.align_combo.setCurrentIndex(index)
        self.align_combo.currentTextChanged.connect(self.on_align_change)
        form_layout.addRow("Position Preset:", self.align_combo)
        
        # Window Height
        self.height_spin = QSpinBox()
        self.height_spin.setRange(50, 300)
        self.height_spin.setValue(self.config_manager.get("window_height"))
        self.height_spin.valueChanged.connect(self.on_height_change)
        form_layout.addRow("Window Height:", self.height_spin)

        # Lock Window
        self.lock_check = QCheckBox("Lock Window Position")
        self.lock_check.setChecked(self.config_manager.get("locked"))
        self.lock_check.toggled.connect(self.on_lock_change)
        form_layout.addRow("", self.lock_check)

        # Click Through
        self.click_through_check = QCheckBox("Click-Through Mode")
        self.click_through_check.setChecked(self.config_manager.get("click_through"))
        self.click_through_check.toggled.connect(self.on_click_through_change)
        form_layout.addRow("", self.click_through_check)
        
        info_label = QLabel("Note: In Click-Through mode, use the System Tray icon to access settings.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addLayout(form_layout)
        layout.addWidget(info_label)
        
        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def on_font_change(self, font):
        self.config_manager.set("font_family", font.family())

    def on_size_change(self, value):
        self.config_manager.set("font_size", value)

    def choose_color(self):
        current_color = QColor(self.config_manager.get("text_color"))
        color = QColorDialog.getColor(current_color, self, "Choose Text Color")
        
        if color.isValid():
            hex_color = color.name()
            self.config_manager.set("text_color", hex_color)
            self.update_color_btn_style()

    def update_color_btn_style(self):
        color = self.config_manager.get("text_color")
        self.color_btn.setStyleSheet(f"background-color: {color}; color: {'black' if QColor(color).lightness() > 128 else 'white'};")

    def on_lock_change(self, checked):
        self.config_manager.set("locked", checked)

    def on_click_through_change(self, checked):
        if checked:
            QMessageBox.information(self, "Click-Through Mode", 
                                    "You are enabling Click-Through mode.\n\n"
                                    "You will NOT be able to click or move the lyrics window.\n"
                                    "Use the System Tray icon (bottom right) to access settings or disable this mode.")
        self.config_manager.set("click_through", checked)

    def on_provider_change(self, text):
        self.config_manager.set("provider", text)

    def on_align_change(self, text):
        self.config_manager.set("alignment", text)

    def on_height_change(self, value):
        self.config_manager.set("window_height", value)
