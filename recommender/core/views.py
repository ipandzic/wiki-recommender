import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import Counter
from django.http import JsonResponse

from core.models import CandidatePages, CrawledPages


def get_links_with_beautiful_soup(url, max_links=20):
    # Initialize empty list to hold the crawled pages
    crawled_pages = [obj.page for obj in CrawledPages.objects.all()]

    # Fetch and parse the web page
    response = requests.get(url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    all_links = []

    # Extract links from the main content area
    for link in soup.select('div.vector-body a'):
        parent = link.find_parent(['div', 'span'], {'class': 'reflist', 'id': ['References', 'Citations']})
        if parent:
            continue  # Skip links under "References" section

        href = link.get('href')
        if href:
            full_url = urljoin(url, href.split('#')[0])

            # Apply multiple exclusion conditions
            if (full_url in crawled_pages or
                    full_url.startswith("https://en.wikipedia.org/wiki/Wikipedia") or
                    "(disambiguation)" in full_url or
                    full_url.endswith('.png') or
                    "(identifier)" in full_url or
                    full_url in ["https://en.wikipedia.org/wiki/Surname", "https://en.wikipedia.org/wiki/Given_name"]):
                continue

            all_links.append(full_url)

            if not CandidatePages.objects.filter(page=full_url).exists():
                CandidatePages.objects.create(page=full_url, rate=0)

    # Count the frequency of each link
    link_count = Counter(all_links)

    # Get the most common links based on their frequency
    most_common_links = [item[0] for item in link_count.most_common(max_links)]

    # Add the URL to the CrawledPages table, making it eligible for future crawling
    if not CrawledPages.objects.filter(page=url).exists():
        CrawledPages.objects.create(page=url)

    return most_common_links


def get_recommended_links(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({"error": "URL parameter is missing."}, status=400)

    links = get_links_with_beautiful_soup(url)
    return JsonResponse({"recommended_links": links})