"""
news_processor.py

Модуль для обработки новостного контента: очистка текста, кластеризация постов,
извлечение ключевых фраз (с помощью упрощённой реализации RAKE) и генерация осмысленных
названий кластеров. Реализована также функция для продвинутой кластеризации с использованием
эмбеддингов от SentenceTransformer и алгоритма HDBSCAN.
"""

import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import nltk
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer
import hdbscan
from keybert import KeyBERT

def ensure_stopwords():
    from nltk.corpus import stopwords
    from nltk import download

    try:
        _ = stopwords.words("english")
        print("✅ Stopwords уже установлены.")
    except LookupError:
        print("⬇️  Stopwords не найдены. Загружаю...")
        download("stopwords")
        try:
            _ = stopwords.words("english")
            print("✅ Stopwords успешно загружены.")
        except LookupError:
            print("❌ Не удалось загрузить stopwords.")
ensure_stopwords()

def clean_text(text):
    """
    Применяет базовую очистку текста.
    
    Удаляет лишние пробелы и символы, отличные от букв и цифр, и приводит строку к нижнему регистру.
    
    :param text: Исходный текст.
    :return: Очищенный текст.
    """
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Zа-яА-Я0-9\s]', '', text)
    return text.lower().strip()

def fetch_user_news(reddit_instance, limit=50):
    """
    Получает новости из Reddit.
    
    Сначала пытается получить новости из персональной ленты пользователя, а при отсутствии
    обращается к сабреддиту "all". Формирует список постов с основными атрибутами.
    
    :param reddit_instance: Объект для доступа к Reddit (PRAW instance).
    :param limit: Максимальное число постов для выборки.
    :return: Кортеж (posts, fallback_used), где posts — список постов, fallback_used — булевый флаг.
    """
    posts = []
    fallback_used = False
    # Пробуем получить новости из персональной ленты
    submissions = list(reddit_instance.front.hot(limit=limit))
    if not submissions:
        fallback_used = True
        submissions = reddit_instance.subreddit("all").hot(limit=limit)
    for submission in submissions:
        post = {
            "title": submission.title or "",
            "selftext": submission.selftext or "",
            "url": submission.url,
            "permalink": submission.permalink,  # для создания ссылок на пост
            "thumbnail": submission.thumbnail if submission.thumbnail not in ['self', 'default', ''] else None,
            "created": submission.created_utc
        }
        posts.append(post)
    return posts, fallback_used

def preprocess_posts(posts):
    """
    Выполняет предобработку списка постов.
    
    Для каждого поста объединяет заголовок и selftext, очищает полученный текст и,
    если результат пустой, заменяет его на "empty".
    
    :param posts: Список постов.
    :return: Список предобработанных текстов.
    """
    texts = []
    for post in posts:
        combined = (post.get('title', '') + " " + post.get('selftext', '')).strip()
        if not combined:
            combined = post.get('title', '')
        cleaned = clean_text(combined)
        if not cleaned:
            cleaned = "empty"
        texts.append(cleaned)
    return texts

def get_combined_stopwords():
    """
    Объединяет английские и русские стоп-слова, исключая отдельные слова,
    которые могут быть полезны для генерации названий.
    
    :return: Список стоп-слов.
    """
    sw = set(stopwords.words('english')).union(set(stopwords.words('russian')))
    exceptions = {"news", "tech", "sport", "game", "politics"}
    return list(sw.difference(exceptions))

def extract_phrases_rake(text, stop_words):
    """
    Простейшая реализация алгоритма RAKE для извлечения ключевых фраз.
    
    Делит текст на предложения, формирует кандидатные фразы, исключая стоп-слова,
    и оценивает каждую фразу по сумме длин слов в ней.
    
    :param text: Исходный текст.
    :param stop_words: Список стоп-слов.
    :return: Список кортежей (фраза, оценка), отсортированных по убыванию оценки.
    """
    sentences = re.split(r'[.?!;\n]', text)
    phrase_list = []
    for sentence in sentences:
        words = sentence.split()
        phrase = []
        for word in words:
            if word in stop_words:
                if phrase:
                    phrase_list.append(" ".join(phrase))
                    phrase = []
            else:
                phrase.append(word)
        if phrase:
            phrase_list.append(" ".join(phrase))
    phrase_scores = []
    for phrase in phrase_list:
        words = phrase.split()
        if words:
            score = sum(len(w) for w in words)
            phrase_scores.append((phrase, score))
    phrase_scores.sort(key=lambda x: x[1], reverse=True)
    return phrase_scores

def extract_keywords_keybert(text, keyphrase_ngram_range=(1, 3), top_n=1):
    """
    Извлекает ключевые фразы из текста с помощью KeyBERT.
    
    :param text: Объединённый текст для анализа.
    :param keyphrase_ngram_range: Диапазон n-грамм, который будет рассматриваться (например, от 1 до 3).
    :param top_n: Число ключевых фраз, которые нужно вернуть.
    :return: Список кортежей (ключевая фраза, оценка).
    """
    kw_model = KeyBERT()
    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=keyphrase_ngram_range, stop_words='english', top_n=top_n)
    return keywords

def generate_cluster_name_keybert(docs):
    """
    Генерирует название кластера с использованием KeyBERT.
    
    Объединяет список документов в один текст и извлекает наиболее значимую ключевую фразу.
    
    :param docs: Список предобработанных текстов для кластера.
    :return: Извлечённая ключевая фраза или None, если не удалось получить кандидата.
    """
    combined_text = " ".join(docs)
    keywords = extract_keywords_keybert(combined_text, keyphrase_ngram_range=(1, 3), top_n=1)
    if keywords:
        return keywords[0][0]  # возвращает саму ключевую фразу
    return None

def improved_hybrid_generate_cluster_names(clusters):
    """
    Генерирует осмысленные названия кластеров с использованием гибридного подхода.
    
    Для каждого кластера:
      1. Объединяются все тексты (заголовки и selftext) постов.
      2. Применяется TF-IDF для выбора слова с наивысшей средней оценкой.
      3. Применяется RAKE для извлечения ключевых фраз.
      4. Если RAKE возвращает фразу, состоящую минимум из двух слов, она используется как название;
         иначе берется слово из TF-IDF.
      5. Если кандидатное название не найдено, возвращается "Кластер X".
    
    :param clusters: Словарь кластеров вида {cluster_id: [posts]}.
    :return: Словарь названий кластеров вида {cluster_id: "Название"}.
    """
    combined_stopwords = get_combined_stopwords()
    cluster_names = {}
    for cluster_id, posts in clusters.items():
        docs = []
        for post in posts:
            combined = (post.get('title', '') + " " + post.get('selftext', '')).strip()
            cleaned = clean_text(combined)
            if cleaned:
                docs.append(cleaned)
        if not docs:
            cluster_names[cluster_id] = f"Кластер {cluster_id}"
            continue

        # TF-IDF часть
        tfidf_word = None
        try:
            vectorizer = TfidfVectorizer(stop_words=combined_stopwords)
            X = vectorizer.fit_transform(docs)
            feature_names = vectorizer.get_feature_names_out()
            avg_scores = X.mean(axis=0).A1
            if len(avg_scores) > 0:
                best_idx = avg_scores.argmax()
                candidate = feature_names[best_idx]
                if len(candidate) >= 3:
                    tfidf_word = candidate
        except Exception as e:
            print(f"TF-IDF error in cluster {cluster_id}: {e}")

        # KeyBERT часть
        keybert_phrase = generate_cluster_name_keybert(docs)
        # Выбор: отдаем приоритет KeyBERT-фразе, если она состоит из 2 и более слов,
        # иначе берем TF-IDF слово.
        if keybert_phrase and len(keybert_phrase.split()) > 1:
            chosen = keybert_phrase
        elif tfidf_word:
            chosen = tfidf_word
        else:
            chosen = f"Кластер {cluster_id}"
        cluster_names[cluster_id] = chosen.title()
    return cluster_names


def remove_markdown_links(text):
    """
    Преобразует Markdown-ссылки вида [текст](url) в простой текст, оставляя только отображаемый текст.
    
    :param text: Исходный текст с Markdown-ссылками.
    :return: Текст без Markdown-ссылок.
    """
    return re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)

def summarize_post(post, max_length=200):
    """
    Формирует краткое содержание поста.
    
    Выбирается текст selftext (если он существует) или заголовок. Удаляются артефакты Markdown (например, звёздочки)
    и преобразуются ссылки. Текст обрезается так, чтобы не разрывать слово, и добавляются многоточия при необходимости.
    
    :param post: Словарь с данными поста.
    :param max_length: Максимальное число символов для содержания.
    :return: Краткое содержание поста.
    """
    text = post.get('selftext') or post.get('title', '')
    text = re.sub(r'\*+', '', text)
    text = remove_markdown_links(text)
    if len(text) <= max_length:
        return text.strip()
    cutoff = text.rfind(' ', 0, max_length)
    if cutoff == -1:
        cutoff = max_length
    summary = text[:cutoff].rstrip() + "..."
    return summary

def cluster_posts_advanced(posts, min_cluster_size=3, metric='euclidean'):
    """
    Продвинутая кластеризация постов с использованием эмбеддингов от SentenceTransformer
    и алгоритма HDBSCAN.
    
    Для каждого поста объединяются заголовок и selftext, затем с помощью модели SentenceTransformer
    генерируются эмбеддинги. Кластеризация выполняется алгоритмом HDBSCAN с параметрами, заданными пользователем.
    В результате каждому посту присваивается метка кластера (значение -1 означает, что пост признан шумом).
    
    :param posts: Список постов.
    :param min_cluster_size: Минимальный размер кластера, используемый HDBSCAN (по умолчанию 3).
    :param metric: Метрика для расчёта расстояний (по умолчанию 'euclidean').
    :return: Кортеж (posts, labels), где posts — обновлённый список с метками кластеров, а labels — массив меток.
    """
    texts = []
    for post in posts:
        combined = (post.get('title', '') + " " + post.get('selftext', '')).strip()
        texts.append(combined if combined else "empty")
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts, convert_to_tensor=True)
    
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric=metric)
    labels = clusterer.fit_predict(embeddings.cpu().numpy())
    
    for i, post in enumerate(posts):
        post['cluster'] = int(labels[i])
    return posts, labels

def cluster_posts(posts, n_clusters=5):
    """
    Выполняет кластеризацию постов с использованием TF-IDF и алгоритма KMeans.
    
    Тексты постов сначала подвергаются предобработке, затем векторизуются, и модель KMeans
    разбивает их на заданное число кластеров. Результатом является список постов с добавленным
    полем 'cluster'.
    
    :param posts: Список постов.
    :param n_clusters: Желаемое число кластеров.
    :return: Кортеж (posts, labels), где labels — метки кластеров для каждого поста.
    :raises ValueError: Если тексты пустые или векторизатор не сформировал словарь.
    """
    texts = preprocess_posts(posts)
    if all(not t.strip() for t in texts):
        raise ValueError("Все документы пустые после предобработки.")
    vectorizer = TfidfVectorizer(stop_words=get_combined_stopwords())
    X = vectorizer.fit_transform(texts)
    if not vectorizer.vocabulary_:
        raise ValueError("Словарь пустой. Возможно, тексты содержат только стоп-слова или пусты.")
    model = KMeans(n_clusters=n_clusters, random_state=42)
    model.fit(X)
    labels = model.labels_
    for i, post in enumerate(posts):
        post['cluster'] = int(labels[i])
    return posts, labels
