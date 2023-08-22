from django.http import JsonResponse
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
import scrapy


class WikipediaSpider(scrapy.Spider):
    global rate
    name = 'wikipedia'

    def parse(self, response):
        parsed_uri = urlparse(self.start_urls[0])
        self.base_url = '{{uri.scheme}}://{{uri.netloc}}'.format(uri=parsed_uri)

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


def get_recommended_links(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({"error": "URL parameter is missing."}, status=400)

    runner = CrawlerRunner()
    deferred = runner.crawl(WikipediaSpider, start_urls=[url])
    deferred.addBoth(lambda _: reactor.stop())  # Stops the Twisted reactor once crawling is done
    reactor.run()  # Blocks here until crawling is done

    links = deferred.result  # This will contain the scraped data

    return JsonResponse({"recommended_links": links})
