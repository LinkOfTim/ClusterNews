# gui/loading_view.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt

class LoadingView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        label = QLabel("Загрузка новостей, пожалуйста подождите...")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # режим неопределенного прогресса
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
