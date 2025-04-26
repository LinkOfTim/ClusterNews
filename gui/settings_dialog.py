# gui/settings_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QPushButton, QMessageBox, QTabWidget, QWidget, QComboBox, QFontComboBox, QSpinBox
)
from PyQt5.QtGui import QFont

class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.current_settings = current_settings  # Словарь с текущими настройками
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Вкладка "Общие"
        general_tab = QWidget()
        general_layout = QVBoxLayout()

        posts_layout = QHBoxLayout()
        posts_layout.addWidget(QLabel("Количество постов:"))
        self.posts_edit = QLineEdit(str(self.current_settings.get("post_limit", 50)))
        posts_layout.addWidget(self.posts_edit)
        general_layout.addLayout(posts_layout)

        general_tab.setLayout(general_layout)
        self.tabs.addTab(general_tab, "Общие")

        # Вкладка "Внешний вид"
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout()

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Blue"])
        self.theme_combo.setCurrentText(self.current_settings.get("theme", "Light"))
        theme_layout.addWidget(self.theme_combo)
        appearance_layout.addLayout(theme_layout)

        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Шрифт:"))
        self.font_combo = QFontComboBox()
        current_font = self.current_settings.get("font", "Arial")
        self.font_combo.setCurrentFont(QFont(current_font))
        font_layout.addWidget(self.font_combo)
        appearance_layout.addLayout(font_layout)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Размер шрифта:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 36)
        self.font_size_spin.setValue(self.current_settings.get("font_size", 10))
        size_layout.addWidget(self.font_size_spin)
        appearance_layout.addLayout(size_layout)

        appearance_tab.setLayout(appearance_layout)
        self.tabs.addTab(appearance_tab, "Внешний вид")

        layout.addWidget(self.tabs)

        # Кнопки OK/Отмена
        buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_settings(self):
        try:
            post_limit = int(self.posts_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Количество постов должно быть числом!")
            return None

        theme = self.theme_combo.currentText()
        font = self.font_combo.currentFont().family()
        font_size = self.font_size_spin.value()

        return {
            "post_limit": post_limit,
            "theme": theme,
            "font": font,
            "font_size": font_size
        }
