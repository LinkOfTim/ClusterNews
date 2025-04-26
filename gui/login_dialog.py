# gui/login_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from config_manager import load_config, save_config, update_config
import auth

DEFAULT_CLIENT_ID = 'GNMeEojrAMPFuBUjvhMLwA'
DEFAULT_CLIENT_SECRET = 'r5oJSCtjWy62s-EPp5a8hZDUqV0mJg'

class LoginDialog(QDialog):
    def __init__(self, initial_username="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("ClusterNews - Авторизация Reddit")
        self.setFixedSize(300, 150)
        layout = QVBoxLayout()
        
        self.label = QLabel("Введите ваш Reddit username:")
        layout.addWidget(self.label)
        
        self.username_edit = QLineEdit(initial_username)
        layout.addWidget(self.username_edit)
        
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_button)
        
        self.setLayout(layout)
        self.reddit_instance = None
        
    def attempt_login(self):
        username = self.username_edit.text().strip()
        if not username:
            QMessageBox.warning(self, "Ошибка", "Введите ваш Reddit username!")
            return
        try:
            reddit, tokens = auth.reddit_login_with_credentials(
                DEFAULT_CLIENT_ID,
                DEFAULT_CLIENT_SECRET,
                username
            )
            QMessageBox.information(self, "Успех", "Авторизация прошла успешно!")
            self.reddit_instance = reddit
            # Сохраняем имя и refresh_token в конфигурации
            update_config({
                "username": username,
                "refresh_token": tokens.get("refresh_token")
            })
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка авторизации", str(e))
