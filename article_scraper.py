import requests
from utils.logger import get_logger
import argparse
from datetime import datetime, timedelta

logger = get_logger("article_scraper")

from database.models.article import Article
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from database.main import DatabaseManager


def take_screenshot(url, output_path):
    logger.info(f"Taking screenshot of {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path=output_path, full_page=True)
        browser.close()
    logger.info(f"Screenshot saved to {output_path}")


def get_hacker_news_articles(url, num_articles):
    logger.info(f"Fetching {num_articles} articles from {url}")
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

    logger.info(f"Retrieved {len(articles)} articles")
    return articles


def get_article_content(article: Article):
    logger.info(f"Fetching content for article: {article.title}")
    response = requests.get(article.url)
    soup = BeautifulSoup(response.text, "html.parser")
    article.content = soup.find_all("p")
    return article


def get_article_screenshot(day: str, article: Article):
    logger.info(f"Getting screenshot for article: {article.title}")
    screenshot_path = f"screenshots/{day}/{article.hn_id}.png"
    take_screenshot(article.url, screenshot_path)
    article.screenshot_path = screenshot_path
    return article


def get_article_type(article: Article):
    logger.info(f"Determining type for article: {article.title}")
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
    logger.info(f"Article type determined: {article.file_type}")
    return article


def parse_arguments():
    parser = argparse.ArgumentParser(description="Scrape articles from Hacker News for a specific day.")
    parser.add_argument('--day', type=str, help='The day to scrape articles for (YYYY-MM-DD format). If not provided, defaults to today.')
    return parser.parse_args()


if __name__ == "__main__":
    logger.info("Starting article scraper")
    args = parse_arguments()
    
    db_manager = DatabaseManager()
    db_manager.create_tables()
    
    if args.day:
        day = args.day
        date = datetime.strptime(day, "%Y-%m-%d")
    else:
        date = datetime.now()
        day = date.strftime("%Y-%m-%d")
    
    url = f"https://news.ycombinator.com/front?day={day}"
    logger.info(f"Scraping articles for date: {day}")
    
    articles = get_hacker_news_articles(url, 10)
    with db_manager.get_session() as session:
        for article in articles:
            logger.info(f"Processing article: {article.title}")
            article.day = day
            article = get_article_type(article)
            if article.is_webpage:
                article = get_article_screenshot(day, article)
            session.merge(article)
        logger.info("Committing changes to database")
        session.commit()
    logger.info("Article scraping completed")
