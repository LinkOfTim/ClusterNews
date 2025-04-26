# gui/main_window.py

import sys
import requests
from io import BytesIO
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QListWidget, QLabel, QTextEdit,
    QHBoxLayout, QListWidgetItem, QMessageBox, QPushButton, QStackedWidget,
    QScrollArea, QApplication, QStyledItemDelegate, QStyle
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QFontMetrics, QPainter
import news_processor
from gui.settings_dialog import SettingsDialog
from gui.loading_view import LoadingView
from config_manager import clear_account_data, update_config, load_config

# Стиль для Light-темы (пустой, стандартный)
LIGHT_STYLE = ""

# Стиль для Dark-темы
DARK_STYLE = """
    QWidget { background-color: #2b2b2b; color: #f0f0f0; }
    QPushButton { background-color: #3c3c3c; color: #f0f0f0; }
    QListWidget, QListView, QAbstractItemView { background-color: #3c3c3c; color: #f0f0f0; }
    QListWidget::item:hover, QListView::item:hover, QAbstractItemView::item:hover { background-color: #505050; }
    QListWidget::item:selected, QListView::item:selected, QAbstractItemView::item:selected { background-color: #0078D7; color: #ffffff; }
    QTextEdit { background-color: #3c3c3c; color: #f0f0f0; }
"""

# Стиль для Blue-темы
BLUE_STYLE = """
    QWidget { background-color: #e0f7fa; color: #006064; }
    QPushButton { background-color: #4dd0e1; color: #004d40; }
    QListWidget { background-color: #4dd0e1; color: #004d40; }
    QListWidget::item { padding: 8px; }
    QListWidget::item:selected { background-color: #006064; color: #ffffff; }
    QListWidget::item:hover { background-color: #80deea; }
    QTextEdit { background-color: #4dd0e1; color: #004d40; }
"""

def update_widget_fonts(widget: QWidget, new_font):
    """
    Рекурсивно обновляет шрифт для данного виджета и всех его дочерних виджетов.
    
    :param widget: Виджет, для которого нужно обновить шрифты.
    :param new_font: Новый объект QFont, который устанавливается для виджета.
    """
    widget.setFont(new_font)
    for child in widget.findChildren(QWidget):
        update_widget_fonts(child, new_font)

class MultiLineDelegate(QStyledItemDelegate):
    """
    Делегат для QListWidget, позволяющий правильно отображать многострочный текст.
    
    Отвечает за отрисовку текста с переносом строк и изменение цвета при выделении.
    """
    def paint(self, painter: QPainter, option, index):
        """
        Переопределение метода отрисовки элемента списка.
        
        :param painter: QPainter, используемый для отрисовки.
        :param option: Параметры опций элемента.
        :param index: Модельный индекс элемента списка.
        """
        painter.save()
        text = index.data(Qt.DisplayRole)
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())
        fm = QFontMetrics(option.font)
        text_wrapped = fm.elidedText(text, Qt.ElideNone, option.rect.width())
        painter.drawText(option.rect, Qt.TextWordWrap, text_wrapped)
        painter.restore()

    def sizeHint(self, option, index):
        """
        Рассчитывает рекомендуемый размер элемента списка с учетом многострочного текста.
        
        :param option: Параметры опций элемента.
        :param index: Модельный индекс элемента списка.
        :return: Размер (QSize), необходимый для отображения текста.
        """
        text = index.data(Qt.DisplayRole)
        fm = QFontMetrics(option.font)
        width = option.rect.width()
        text_rect = fm.boundingRect(0, 0, width, 0, Qt.TextWordWrap, text)
        return QSize(width, text_rect.height() + 10)

class MainView(QWidget):
    """
    Основное представление приложения, содержащее списки кластеров и постов.
    
    Реализует методы для заполнения списков и обработки кликов по элементам.
    """
    def __init__(self, parent):
        """
        Инициализирует MainView и сохраняет ссылку на главное окно.
        
        :param parent: Родительский объект, обычно MainWindow.
        """
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """
        Создает и настраивает пользовательский интерфейс MainView.
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Верхняя панель с кнопками для обновления, настроек и выхода
        top_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Обновить новости")
        self.refresh_button.clicked.connect(self.parent.load_news)
        top_layout.addWidget(self.refresh_button)

        self.settings_button = QPushButton("Настройки")
        self.settings_button.clicked.connect(self.parent.open_settings)
        top_layout.addWidget(self.settings_button)

        self.logout_button = QPushButton("Сменить аккаунт / Выйти")
        self.logout_button.clicked.connect(self.parent.logout)
        top_layout.addWidget(self.logout_button)

        layout.addLayout(top_layout)

        # Основная панель со списками кластеров и постов
        main_layout = QHBoxLayout()
        self.cluster_list = QListWidget()
        self.cluster_list.setMaximumWidth(300)
        self.cluster_list.setStyleSheet("""
            QListWidget::item { border-bottom: 1px solid #cccccc; padding: 8px; }
            QListWidget::item:selected { background-color: #0078D7; color: #ffffff; }
        """)
        self.cluster_list.itemClicked.connect(self.display_posts_for_cluster)
        main_layout.addWidget(self.cluster_list)

        self.post_list = QListWidget()
        self.post_list.setStyleSheet("""
            QListWidget::item { border-bottom: 1px solid #cccccc; padding: 8px; }
            QListWidget::item:selected { background-color: #0078D7; color: #ffffff; }
        """)
        self.post_list.itemDoubleClicked.connect(self.parent.show_post_details)
        main_layout.addWidget(self.post_list)

        layout.addLayout(main_layout)
        self.setLayout(layout)

        # Устанавливаем делегат для многострочного отображения текста
        delegate = MultiLineDelegate(self)
        self.cluster_list.setItemDelegate(delegate)
        self.cluster_list.setWordWrap(True)
        self.post_list.setItemDelegate(delegate)
        self.post_list.setWordWrap(True)

    def populate_clusters(self, clusters, cluster_names):
        """
        Заполняет список кластеров с именами и количеством постов.

        :param clusters: Словарь кластеров вида {cluster_id: [posts]}.
        :param cluster_names: Словарь названий кластеров вида {cluster_id: "Название"}.
        """
        self.cluster_list.clear()
        for cluster_id in sorted(clusters.keys()):
            name = cluster_names.get(cluster_id, f"Кластер {cluster_id}")
            item = QListWidgetItem(f"{name} ({len(clusters[cluster_id])} постов)")
            item.setData(Qt.UserRole, cluster_id)
            self.cluster_list.addItem(item)

    def display_posts_for_cluster(self, item):
        """
        Отображает список постов для выбранного кластера при клике на элементе списка.
        
        :param item: Выбранный элемент из списка кластеров.
        """
        cluster_id = item.data(Qt.UserRole)
        posts = self.parent.clusters.get(cluster_id, [])
        self.post_list.clear()
        for post in posts:
            list_item = QListWidgetItem(post['title'])
            list_item.setData(Qt.UserRole, post)
            self.post_list.addItem(list_item)

class DetailView(QWidget):
    """
    Представление для детального просмотра выбранного поста.
    
    Отображает заголовок, изображение (если есть), краткое содержание и ссылку на оригинальный пост.
    """
    def __init__(self, parent):
        """
        Инициализирует DetailView и сохраняет ссылку на главное окно.
        
        :param parent: Родительский объект (MainWindow).
        """
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """
        Настраивает пользовательский интерфейс для детального просмотра.
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        self.back_button = QPushButton("Назад")
        self.back_button.clicked.connect(self.parent.show_main_view)
        layout.addWidget(self.back_button)

        # Создаем скроллируемую область для контента
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(10)
        content.setLayout(self.content_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def populate_details(self, post):
        """
        Заполняет детальное представление данными из поста.

        :param post: Словарь с данными поста (заголовок, selftext, thumbnail, permalink и т.д.).
        """
        # Очистка предыдущего контента
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        title_label = QLabel(f"<h2>{post['title']}</h2>")
        title_label.setTextFormat(Qt.RichText)
        title_label.setWordWrap(True)
        self.content_layout.addWidget(title_label)

        if post.get('thumbnail'):
            try:
                response = requests.get(post['thumbnail'], timeout=5)
                if response.status_code == 200:
                    image_data = BytesIO(response.content)
                    pixmap = QPixmap()
                    if pixmap.loadFromData(image_data.read()):
                        scaled = pixmap.scaledToWidth(200, Qt.SmoothTransformation)
                        img_label = QLabel()
                        img_label.setPixmap(scaled)
                        self.content_layout.addWidget(img_label)
            except Exception as e:
                print("Ошибка загрузки изображения:", e)

        summary = news_processor.summarize_post(post)
        summary_label = QLabel("Краткое содержание:")
        self.content_layout.addWidget(summary_label)
        summary_text = QTextEdit()
        summary_text.setReadOnly(True)
        summary_text.setText(summary)
        self.content_layout.addWidget(summary_text)

        reddit_link = f"https://www.reddit.com{post.get('permalink', '')}"
        link_label = QLabel(f"<a href='{reddit_link}'>Открыть пост на Reddit</a>")
        link_label.setOpenExternalLinks(True)
        self.content_layout.addWidget(link_label)

class MainWindow(QMainWindow):
    """
    Главное окно приложения ClusterNews, которое объединяет все представления.
    
    Отвечает за загрузку новостей, применение внешнего вида, навигацию между экранами и сохранение настроек.
    """
    def __init__(self, reddit_instance):
        """
        Инициализирует MainWindow, загружает сохранённые настройки и создаёт основные представления.
        
        :param reddit_instance: Объект PRAW для доступа к данным Reddit.
        """
        super().__init__()
        self.reddit_instance = reddit_instance
        config = load_config()
        self.settings = {
            "post_limit": config.get("post_limit", 50),
            "theme": config.get("theme", "Light"),
            "font": config.get("font", "Arial"),
            "font_size": config.get("font_size", 10)
        }

        self.setWindowTitle("ClusterNews")
        self.setGeometry(100, 100, 1200, 800)
        self.posts = []
        self.clusters = {}      # cluster_id -> список постов
        self.cluster_names = {} # cluster_id -> название кластера

        self.stack = QStackedWidget()
        self.loading_view = LoadingView()
        self.main_view = MainView(self)
        self.detail_view = DetailView(self)
        self.stack.addWidget(self.loading_view)
        self.stack.addWidget(self.main_view)
        self.stack.addWidget(self.detail_view)
        self.setCentralWidget(self.stack)

        self.apply_appearance()
        self.load_news()

    def open_settings(self):
        """
        Открывает диалог настроек. При подтверждении обновляет внешнее оформление, загружает новости
        и сохраняет новые параметры в конфигурацию.
        """
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_():
            new_settings = dialog.get_settings()
            if new_settings:
                self.settings = new_settings
                self.apply_appearance()
                self.load_news()
                config = load_config()
                config.update(new_settings)
                update_config(config)

    def apply_appearance(self):
        """
        Применяет настройки внешнего вида: тема, шрифт и размер шрифта.
        Обновляет глобальные стили, а также обновляет шрифты у всех виджетов.
        """
        theme = self.settings.get("theme", "Light")
        if theme == "Light":
            self.setStyleSheet(LIGHT_STYLE)
        elif theme == "Dark":
            self.setStyleSheet(DARK_STYLE)
        elif theme == "Blue":
            self.setStyleSheet(BLUE_STYLE)

        font_family = self.settings.get("font", "Arial")
        font_size = self.settings.get("font_size", 10)
        new_font = self.font()
        new_font.setFamily(font_family)
        new_font.setPointSize(font_size)
        QApplication.setFont(new_font)
        update_widget_fonts(self, new_font)

    def load_news(self):
        """
        Загружает новости, выполняет кластеризацию и генерирует названия кластеров.
        При загрузке отображается индикатор, а по завершении переключается в главное представление.
        """
        try:
            self.stack.setCurrentWidget(self.loading_view)
            QApplication.processEvents()

            self.posts, fallback = news_processor.fetch_user_news(self.reddit_instance, limit=self.settings.get("post_limit", 50))
            if fallback:
                QMessageBox.information(self, "Информация",
                    "Ваша лента пуста (вы не подписаны ни на какие сабреддиты).\nПоказаны новости из /r/all.")
            self.posts, _ = news_processor.cluster_posts_advanced(self.posts)
            self.clusters = {}
            for post in self.posts:
                cid = post['cluster']
                self.clusters.setdefault(cid, []).append(post)
            self.cluster_names = news_processor.improved_hybrid_generate_cluster_names(self.clusters)
            self.main_view.populate_clusters(self.clusters, self.cluster_names)
            self.main_view.post_list.clear()
            self.stack.setCurrentWidget(self.main_view)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить новости: {e}")

    def show_post_details(self, item):
        """
        При двойном клике по посту отображает детальную информацию об этом посте.
        
        :param item: Элемент списка, содержащий данные выбранного поста.
        """
        post = item.data(Qt.UserRole)
        self.detail_view.populate_details(post)
        self.stack.setCurrentWidget(self.detail_view)

    def show_main_view(self):
        """
        Переключается обратно в основное представление с кластерами и постами.
        """
        self.stack.setCurrentWidget(self.main_view)

    def logout(self):
        """
        Выполняет выход из аккаунта, очищая сохраненные данные аккаунта и закрывая окно.
        """
        clear_account_data()
        self.close()
