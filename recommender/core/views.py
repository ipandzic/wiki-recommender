import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from django.http import JsonResponse

from core.models import CandidatePages, CrawledPages


def get_links_with_beautiful_soup(url):
    # Check if the URL has been already crawled
    if CrawledPages.objects.filter(page=url).exists():
        return []

    # Fetch and parse the web page
    response = requests.get(url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    base_url = url

    recommended_links = []

    # Extract links from the main content area
    for link in soup.select('div.vector-body a'):
        parent = link.find_parent(['div', 'span'], {'class': 'reflist', 'id': ['References', 'Citations']})
        if parent:
            continue  # Skip links under "References" section

        href = link.get('href')
        if href:
            full_url = urljoin(base_url, href.split('#')[0])
            recommended_links.append(full_url)

            # Add to CandidatePages if not already there
            if not CandidatePages.objects.filter(page=full_url).exists():
                CandidatePages.objects.create(page=full_url, rate=0)  # Set initial rate to 0

    # Extract external links
    for link in soup.select('a.external.text'):
        parent = link.find_parent(['div', 'span'], {'class': 'reflist', 'id': ['References', 'Citations']})
        if parent:
            continue  # Skip links under "References" section

        href = link.get('href')
        if href and href[:2] != '//':
            recommended_links.append(href)

            # Add to CandidatePages if not already there
            if not CandidatePages.objects.filter(page=href).exists():
                CandidatePages.objects.create(page=href, rate=0)  # Set initial rate to 0

    # Mark the URL as crawled
    CrawledPages.objects.create(page=url)

    return recommended_links


def get_recommended_links(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({"error": "URL parameter is missing."}, status=400)

    links = get_links_with_beautiful_soup(url)
    return JsonResponse({"recommended_links": links})
