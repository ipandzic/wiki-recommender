import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from django.http import JsonResponse


def get_links_with_beautiful_soup(url):
    response = requests.get(url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    base_url = url

    recommended_links = []

    # Extract links from the main content area
    for link in soup.select('div.vector-body a'):
        href = link.get('href')
        if href:
            full_url = urljoin(base_url, href.split('#')[0])
            recommended_links.append(full_url)

    # Extract external links
    for link in soup.select('a.external.text'):
        href = link.get('href')
        if href and href[:2] != '//':
            recommended_links.append(href)

    return recommended_links


def get_recommended_links(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({"error": "URL parameter is missing."}, status=400)

    links = get_links_with_beautiful_soup(url)
    return JsonResponse({"recommended_links": links})

