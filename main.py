import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from prettytable import PrettyTable

URL = "https://www.vg.no"
TIME_INTERVAL = 180  # 3 minutter

checked_urls = set()


def get_soup(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Feil ved henting av {url}: {response.status_code}")
        return None

    return BeautifulSoup(response.text, "html.parser")


def get_article_info(article):
    link_tag = article.find("a", itemprop="url")
    if not link_tag:
        return None

    article_url = link_tag.get("href").split("?")[0]
    if article_url in checked_urls:
        return None

    article_soup = get_soup(article_url)
    if not article_soup:
        return None

    title = get_article_title(article_soup)
    authors = get_article_authors(article_soup)
    published = get_article_published_date(article_soup)
    lead_text = get_article_lead_text(article_soup)

    # lead_text = "Slått av. Slå på for å se"

    return published, title, lead_text, authors


def get_article_title(article_soup):
    title_tag = (
        article_soup.find("h1", attrs={"data-test-tag": "headline"})
        or article_soup.find("h1", attrs={"data-test-tag": "tittel"})  # for formatting
        or article_soup.find("h1")
    )

    if title_tag:
        return title_tag.get_text(strip=True)

    return None


def get_article_authors(article_soup):
    authors_tag = (
        article_soup.find(attrs={"data-test-tag": "byline:authors"})
        or article_soup.find(rel="author")
        or article_soup.find(class_="fr")
        or article_soup.find(class_="Bn")
    )

    if authors_tag:
        return authors_tag.get_text(strip=True)

    return None


def get_article_published_date(article_soup):
    timestamp_tag = article_soup.find("time", itemprop="dateModified")
    if timestamp_tag:
        timestamp_str = timestamp_tag.get("datetime")
        published = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")

        return published.replace(tzinfo=timezone.utc).astimezone(
            tz=timezone(timedelta(hours=1))
        )

    return None


def get_article_lead_text(article_soup):
    lead_text_tag = article_soup.find(attrs={"data-test-tag": "lead-text"})

    if lead_text_tag:
        return lead_text_tag.get_text(strip=True)

    return None


def process_article(article):
    a_tag = article.find("a", itemprop="url")
    if not a_tag:
        print("No link found for article")
        return

    article_url = a_tag.get("href")
    if article_url in checked_urls:
        return

    article_info = get_article_info(article)
    if article_info:
        checked_urls.add(article_url)
        return article_info


def scrape():
    print("Starter scraping...")

    soup = get_soup(URL)
    if not soup:
        return

    articles = soup.find_all("article")

    # Using a generator to process articles
    processed_articles = (process_article(article) for article in articles[:17])

    # Filtering out None or falsy values and constructing a set
    new_articles = {info for info in processed_articles if info}

    if new_articles:
        table = PrettyTable(["Publisert", "Tittel", "Sammendrag", "Forfatter(e)"])
        for published, title, summary, authors in new_articles:
            table.add_row([published, title, summary, authors])
        print(table)


try:
    while True:
        scrape()
        time.sleep(TIME_INTERVAL)
except KeyboardInterrupt:
    print("Avslutter programmet")
