from urllib.parse import urlparse
from django.http import JsonResponse
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerRunner
from twisted.internet import defer
from channels.db import database_sync_to_async
import scrapy


class WikipediaSpider(scrapy.Spider):
    name = 'wikipedia'

    def parse(self, response):
        parsed_uri = urlparse(self.start_urls[0])
        self.base_url = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

        recommended_links = []

        if response.status == 200:
            for link in response.xpath('//div[@class = "vector-body"]//a'):
                candidate_link = link.xpath('.//@href').get()
                if candidate_link is not None:
                    candidate_link = candidate_link.split('#')[0]
                    if candidate_link != '' and candidate_link[:4] != 'http' and candidate_link[:2] != '//':
                        recommended_links.append(self.base_url + candidate_link)
            for link in response.xpath('//a[@class = "external text"]'):
                candidate_link = link.xpath('.//@href').get()
                if candidate_link != '' and candidate_link[:2] != '//':
                    recommended_links.append(candidate_link)

        return recommended_links


@database_sync_to_async
def run_spider(url):
    runner = CrawlerRunner(get_project_settings())
    deferred = runner.crawl(WikipediaSpider, start_urls=[url])
    result = yield deferred  # Use yield to extract the result from the Deferred
    return result


async def get_recommended_links(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({"error": "URL parameter is missing."}, status=400)

    links = await run_spider(url)

    # Ensure the result is a list before sending it in the JsonResponse
    if not isinstance(links, list):
        links = []

    return JsonResponse({"recommended_links": links})
