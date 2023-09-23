import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from collections import Counter

from django.db.models import F
from django.http import JsonResponse

from core.models import CandidatePages, CrawledPages


def get_recommended_links_view(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({"error": "URL parameter is missing."}, status=400)

    links = get_links_with_beautiful_soup(url)
    return JsonResponse({"recommended_links": links})


def normalize_url(url):
    # Parse the URL and normalize it
    parsed_url = urlparse(url)
    normalized_url = urlunparse(parsed_url._replace(fragment='', query=''))
    return normalized_url.lower()


def get_links_with_beautiful_soup(url, max_links=20):
    # Remove the URL from the CandidatePages table if it exists
    CandidatePages.objects.filter(page=url).delete()
    # Fetch and parse the web page
    normalized_url = normalize_url(url)
    response = requests.get(url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    article_text = soup.get_text()

    # Add the URL to the CrawledPages table
    if not CrawledPages.objects.filter(page=url).exists():
        CrawledPages.objects.create(page=url)

    link_phrases = []
    crawled_pages = [obj.page for obj in CrawledPages.objects.all()]

    for link in soup.select('div.vector-body a'):
        parent = link.find_parent(['div', 'span'], {'class': 'reflist', 'id': ['References', 'Citations']})
        if parent:
            continue

        href = link.get('href')
        if href:
            full_url = urljoin(url, href.split('#')[0])

            if normalize_url(full_url) == normalized_url:
                continue

            if full_url in crawled_pages:
                continue

            # Exclusion conditions
            if (full_url.startswith("https://en.wikipedia.org/wiki/Wikipedia") or
                    "(disambiguation)" in full_url or
                    full_url.endswith('.png') or
                    "(identifier)" in full_url or
                    full_url.startswith("https://en.wikipedia.org/wiki/Category:") or
                    full_url.startswith("https://en.wikipedia.org/wiki/Help:") or
                    full_url.startswith("https://en.wikipedia.org/wiki/File:") or
                    full_url.startswith("https://en.wikipedia.org/wiki/Portal:") or
                    full_url in ["https://en.wikipedia.org/wiki/Surname", "https://en.wikipedia.org/wiki/Given_name"] or
                    full_url.endswith('/') or
                    full_url.split('/')[-1].isdigit() or
                    full_url.lower() == url.lower()):
                continue

            title_phrase = full_url.split('/')[-1].replace('_', ' ')
            link_phrases.append(title_phrase)

            if not CandidatePages.objects.filter(page=full_url).exists():
                CandidatePages.objects.create(page=full_url, rate=1)  # Start with a rate of 1

    # Count occurrences of each title phrase in the text
    phrase_count = Counter(link_phrases)

    for phrase in phrase_count:
        phrase_count[phrase] = 1 + article_text.lower().count(phrase.lower())  # Add 1 to ensure a minimum rate of 1

    # Update the rates
    for phrase, count in phrase_count.items():
        full_url = f"https://en.wikipedia.org/wiki/{phrase.replace(' ', '_')}"
        CandidatePages.objects.filter(page=full_url).update(rate=F('rate') + count)

    # Get CandidatePages URLs and rates, excluding those in CrawledPages
    candidate_pages = CandidatePages.objects.exclude(page__in=crawled_pages).order_by('-rate')[:max_links]

    # Create a list of top links based on the rates
    top_links = [obj.page for obj in candidate_pages]

    # Reset the rate for the selected links to 1
    CandidatePages.objects.filter(page__in=top_links).update(rate=2)

    return top_links
