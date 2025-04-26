import sys
from PyQt5.QtWidgets import QApplication, QDialog
from gui.login_dialog import LoginDialog
from gui.main_window import MainWindow
from config_manager import load_config
import auth

def main():
    app = QApplication(sys.argv)
    config = load_config()
    reddit_instance = None
    if "username" in config and "refresh_token" in config:
        try:
            reddit_instance = auth.reddit_login_from_config(config)
        except Exception as e:
            print(f"Автоматическая авторизация не удалась: {e}")
    if not reddit_instance:
        login_dialog = LoginDialog(initial_username=config.get("username", ""))
        if login_dialog.exec_() == QDialog.Accepted:
            reddit_instance = login_dialog.reddit_instance
        else:
            sys.exit()
    main_window = MainWindow(reddit_instance)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
