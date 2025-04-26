# auth.py

import praw
import webbrowser
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse

# Данные твоего приложения (будут использоваться по умолчанию)
DEFAULT_CLIENT_ID = 'GNMeEojrAMPFuBUjvhMLwA'
DEFAULT_CLIENT_SECRET = 'r5oJSCtjWy62s-EPp5a8hZDUqV0mJg'
REDIRECT_URI = "http://localhost:8080"
USER_AGENT_TEMPLATE = "ClusterNews by /u/{}"

# HTTP-сервер для получения кода авторизации
class OAuthHandler(BaseHTTPRequestHandler):
    authorization_code = None

    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        query_params = urlparse.parse_qs(parsed_path.query)
        if "code" in query_params:
            OAuthHandler.authorization_code = query_params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write("Авторизация прошла успешно! Можно закрыть это окно.")
        else:
            self.send_response(400)
            self.end_headers()

def start_http_server():
    server = HTTPServer(("localhost", 8080), OAuthHandler)
    server.handle_request()  # обработает один запрос
    server.server_close()

def reddit_login_with_credentials(client_id, client_secret, username):
    user_agent = USER_AGENT_TEMPLATE.format(username)
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=REDIRECT_URI,
        user_agent=user_agent
    )
    scopes = ["identity", "read"]
    auth_url = reddit.auth.url(scopes, "random_state_string", "permanent")
    
    # Открываем браузер с URL авторизации
    webbrowser.open(auth_url)

    # Запускаем локальный сервер для получения кода авторизации
    server_thread = threading.Thread(target=start_http_server, daemon=True)
    server_thread.start()
    server_thread.join()

    if OAuthHandler.authorization_code:
        refresh_token = reddit.auth.authorize(OAuthHandler.authorization_code)
        tokens = {"refresh_token": refresh_token}
        return reddit, tokens
    else:
        raise Exception("Не удалось получить код авторизации.")

def reddit_login_from_config(config):
    username = config.get("username")
    refresh_token = config.get("refresh_token")
    if not username or not refresh_token:
        raise Exception("Данные аккаунта отсутствуют в конфигурации.")
    user_agent = USER_AGENT_TEMPLATE.format(username)
    reddit = praw.Reddit(
         client_id=DEFAULT_CLIENT_ID,
         client_secret=DEFAULT_CLIENT_SECRET,
         redirect_uri=REDIRECT_URI,
         user_agent=user_agent,
         refresh_token=refresh_token
    )
    try:
        # Проверяем, можно ли получить данные пользователя
        _ = reddit.user.me()
    except Exception as e:
        raise Exception("Автоматическая авторизация не удалась: " + str(e))
    return reddit
