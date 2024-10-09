import requests
import os

from article import Article
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.sync_api import sync_playwright

def take_screenshot(url, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path=output_path, full_page=True)
        browser.close()

def get_hacker_news_articles(url: str, page_size: int = 0) -> list[Article]:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    articles: list[Article] = []
    for item in soup.find_all('tr', {'class': 'athing'}):
        id = item.get('id')
        if page_size > 0 and len(articles) >= page_size:
            break
        sibling = item.next_sibling.find_all('td', {'class': 'subtext'})
        for subtext in sibling:
            author_element = subtext.find('a', {'class': 'hnuser'})   
            if author_element:
                author = author_element.text
            else:
                author = None
            score_element = subtext.find('span', {'class': 'score'})
            if score_element:
                score = score_element.text
            else:
                score = None
        titleline = item.find_all('span', {'class': 'titleline'})
        for title in titleline:
            articles.append(Article(title.find('a').text, title.find('a')['href'], author, score, id))
    return articles

def get_article_content(article: Article):
    response = requests.get(article.url)
    soup = BeautifulSoup(response.text, 'html.parser')
    article.content = soup.find_all('p')
    return article

def get_article_screenshot(day: str, article: Article):
    take_screenshot(article.url, f"screenshots/{day}/{article.id}.png")

def get_article_type(article: Article):
    if article.url.endswith('/'):
        article.url = article.url[:-1]

    if article.url.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')):
        article.file_type = 'document'
    elif article.url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
        article.file_type = 'image'
    elif article.url.endswith(('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm')):
        article.file_type = 'video'
    else:
        article.is_webpage = True
        article.file_type = 'webpage'
    article.file_extension = article.url.split('/')[-1]
    return article

if __name__ == "__main__":
    date = datetime.now()
    day = date.strftime("%Y-%m-%d")
    url = f"https://news.ycombinator.com/front?day={day}"
    articles = get_hacker_news_articles(url, 10)
    for article in articles:
        article = get_article_type(article)
        if article.is_webpage:
            get_article_screenshot(day, article)
