import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import time
from prettytable import PrettyTable

URL = "https://www.vg.no"

# Sett for å holde styr på hvilke artikler som allerede er sjekket.
checked_urls = set()


# Funksjon for å hente og parse HTML-innholdet fra en gitt URL.
def get_soup(url):
    print(url)

    # Utfører en HTTP GET forespørsel til den gitte URL-en.
    response = requests.get(url)
    if response.status_code == 200:
        # Parser HTML-innholdet og returnerer en BeautifulSoup-objekt.
        return BeautifulSoup(response.text, "html.parser")
    else:
        print(f"Feil ved henting av {url}: {response.status_code}")
        return None


def get_article_info(article):
    link_tag = article.find("a", itemprop="url")
    if not link_tag:
        return None

    # Henter og parser HTML-innholdet fra artikkelens URL.
    article_url = link_tag.get("href").split("?")[0]
    article_soup = get_soup(article_url)
    if not article_soup:
        return None

    # Henter tittel, forfattere, publiseringsdato og sammendrag fra artikkelen.
    title = get_article_title(article_soup, article_url)
    authors = get_article_authors(article_soup)
    published = get_article_published_date(article_soup)
    lead_text = get_article_lead_text(article_soup)

    # slå denne av hvis du vil ha med lede-tekst
    # lead_text = "Slått av. Slå på for å se"

    return published, title, lead_text, authors


def get_article_title(article_soup, article_url):
    h1_tags = article_soup.find_all("h1")

    title_tag = article_soup.find("h1", attrs={"data-test-tag": "headline"})

    # Hvis ingen slik tag ble funnet, finn da den første h1 tagen
    if title_tag is None:
        h1_tags = article_soup.find_all("h1")
        if h1_tags:
            title_tag = h1_tags[0]

    if title_tag:
        return title_tag.get_text(strip=True)
    else:
        return "Ukjent"


def get_article_authors(article_soup):
    # Prøver flere metoder for å finne forfatterinformasjonen.
    authors_tag = article_soup.find(attrs={"data-test-tag": "byline:authors"})
    if authors_tag:
        return authors_tag.get_text(strip=True)

    authors_tag = article_soup.find(rel="author")
    if authors_tag:
        return authors_tag.get_text(strip=True)

    authors_tag = article_soup.find(class_="fr")
    if authors_tag:
        return authors_tag.get_text(strip=True)

    authors_tag = article_soup.find(class_="Bn")
    if authors_tag:
        return authors_tag.get_text(strip=True)

    # Returnerer "Ukjent" hvis forfatterinformasjon ikke blir funnet.
    return "Ukjent"


def get_article_published_date(article_soup):
    # Prøver å finne tiden taggen som inneholder publiseringsdatoen.
    timestamp_tag = article_soup.find("time", itemprop="dateModified")
    if timestamp_tag:
        timestamp_str = timestamp_tag.get("datetime")
        published = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")

        # Konverterer tiden til lokal tidssone.
        return published.replace(tzinfo=timezone.utc).astimezone(
            tz=timezone(timedelta(hours=2))
        )
    else:
        return "Uknown"


def get_article_lead_text(article_soup):
    # Prøver å finne lead text ved å bruke data-test-tag attributtet.
    lead_text_tag = article_soup.find(attrs={"data-test-tag": "lead-text"})
    if lead_text_tag:
        return lead_text_tag.get_text(strip=True)

    # Returnerer "N/A" hvis lead text ikke blir funnet.
    return "N/A"


def scrape():
    print("Starter scraping...")

    # Henter og parser HTML-innholdet fra hovedsiden.
    soup = get_soup(URL)

    if soup:
        # Finner alle artikkel-elementer på siden.
        articles = soup.find_all("article")
        new_articles = []

        for article in articles:
            a_tag = article.find("a", itemprop="url")
            if a_tag is None:
                print("No link found for article")
                continue

            article_url = a_tag.get("href")

            # Sjekker om artikkelen allerede er sjekket.
            if article_url not in checked_urls:
                article_info = get_article_info(article)
                if article_info:
                    # Legger til informasjon om nye artikler til listen.
                    new_articles.append(article_info)
                    checked_urls.add(article_url)

        if new_articles:
            # Skriver ut informasjon om de nye artiklene i en tabell.
            table = PrettyTable(["Publisert", "Tittel", "Sammendrag", "Forfatter(e)"])
            for published, title, summary, authors in new_articles:
                table.add_row([published, title, summary, authors])

            print(table)


try:
    while True:
        scrape()
        # time.sleep(600)  # 10 minutter
        # time.sleep(60)  # 1 minutter
        time.sleep(180)  # 3 minutter
except KeyboardInterrupt:
    print("Avslutter programmet")
