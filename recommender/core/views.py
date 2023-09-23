import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from collections import Counter
from django.http import JsonResponse

from core.models import CandidatePages, CrawledPages


def normalize_url(url):
    # Parse the URL and normalize it
    parsed_url = urlparse(url)
    normalized_url = urlunparse(parsed_url._replace(fragment='', query=''))
    return normalized_url.lower()


def get_links_with_beautiful_soup(url, max_links=20):
    # Fetch and parse the web page
    normalized_url = normalize_url(url)
    response = requests.get(url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    article_text = soup.get_text()  # Get the entire text of the article

    # Add the URL to the CrawledPages table, making it eligible for future crawling
    if not CrawledPages.objects.filter(page=url).exists():
        CrawledPages.objects.create(page=url)

    link_phrases = []
    crawled_pages = [obj.page for obj in CrawledPages.objects.all()]

    # Extract links from the main content area
    for link in soup.select('div.vector-body a'):
        parent = link.find_parent(['div', 'span'], {'class': 'reflist', 'id': ['References', 'Citations']})
        if parent:
            continue  # Skip links under "References" section
        href = link.get('href')
        if href:
            full_url = urljoin(url, href.split('#')[0])
            if normalize_url(full_url) == normalized_url:
                continue

            if full_url in crawled_pages:
                continue
            # Apply exclusion conditions
            if (full_url.startswith("https://en.wikipedia.org/wiki/Wikipedia") or
                "(disambiguation)" in full_url or
                full_url.endswith('.png') or
                "(identifier)" in full_url or
                full_url.startswith("https://en.wikipedia.org/wiki/Category:") or
                full_url in ["https://en.wikipedia.org/wiki/Surname", "https://en.wikipedia.org/wiki/Given_name"] or
                full_url.endswith('/') or
                full_url.split('/')[-1].isdigit() or
                full_url.lower() == url.lower()):
                continue

            if not CandidatePages.objects.filter(page=full_url).exists():
                CandidatePages.objects.create(page=full_url, rate=0)

            # Extract the title phrase from the link and convert underscores to spaces
            title_phrase = full_url.split('/')[-1].replace('_', ' ')

            link_phrases.append(title_phrase)

    # Count occurrences of each title phrase in the text of the initial article
    phrase_count = Counter(link_phrases)
    for phrase in link_phrases:
        phrase_count[phrase] = article_text.lower().count(phrase.lower())

    # Sort by the count and take the top max_links
    sorted_phrases = sorted(phrase_count.items(), key=lambda x: x[1], reverse=True)[:max_links]
    top_links = [
        f"https://en.wikipedia.org/wiki/{phrase.replace(' ', '_')}"
        for phrase, count in sorted_phrases
        if f"https://en.wikipedia.org/wiki/{phrase.replace(' ', '_')}" != url
    ]

    return top_links


def get_recommended_links(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({"error": "URL parameter is missing."}, status=400)

    links = get_links_with_beautiful_soup(url)
    return JsonResponse({"recommended_links": links})