import requests

from database.models.article import Article
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.sync_api import sync_playwright
from database.main import DatabaseManager


def take_screenshot(url, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path=output_path, full_page=True)
        browser.close()


def get_hacker_news_articles(url, num_articles):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    for item in soup.find_all("tr", class_="athing")[:num_articles]:
        id = item["id"]  # We'll use this as a reference, not as the primary key
        title = item.find("span", class_="titleline")
        subtext = item.find_next_sibling("tr").find("td", class_="subtext")
        if title and subtext:
            title_text = title.find("a").text
            url = title.find("a")["href"]
            author = (
                subtext.find("a", class_="hnuser").text
                if subtext.find("a", class_="hnuser")
                else "Unknown"
            )
            score_text = (
                subtext.find("span", class_="score").text
                if subtext.find("span", class_="score")
                else "0 points"
            )
            score = int(score_text.split()[0])
            article = Article(title=title_text, url=url, author=author, score=score)
            article.hn_id = int(id)  # Store the Hacker News ID as a separate attribute
            articles.append(article)

    return articles


def get_article_content(article: Article):
    response = requests.get(article.url)
    soup = BeautifulSoup(response.text, "html.parser")
    article.content = soup.find_all("p")
    return article


def get_article_screenshot(day: str, article: Article):
    screenshot_path = f"screenshots/{day}/{article.hn_id}.png"
    take_screenshot(article.url, screenshot_path)
    article.screenshot_path = screenshot_path
    return article


def get_article_type(article: Article):
    if article.url.endswith("/"):
        article.url = article.url[:-1]

    if article.url.endswith(
        (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx")
    ):
        article.file_type = "document"
    elif article.url.endswith(
        (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp")
    ):
        article.file_type = "image"
    elif article.url.endswith(
        (".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm")
    ):
        article.file_type = "video"
    else:
        article.is_webpage = True
        article.file_type = "webpage"
    if not article.is_webpage:
        article.file_extension = article.url.split("/")[-1]
    return article


if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.create_tables()
    date = datetime.now()
    day = date.strftime("%Y-%m-%d")
    url = f"https://news.ycombinator.com/front?day={day}"
    articles = get_hacker_news_articles(url, 10)
    with db_manager.get_session() as session:
        for article in articles:
            article.day = day
            article = get_article_type(article)
            if article.is_webpage:
                article = get_article_screenshot(day, article)
            session.merge(article)
        session.commit()
