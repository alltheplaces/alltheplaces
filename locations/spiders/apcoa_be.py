from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class ApcoaBESpider(CrawlSpider, StructuredDataSpider):
    name = "apcoa_be"
    item_attributes = {"operator": "APCOA Parking", "operator_wikidata": "Q296108"}
    allowed_domains = ["www.apcoa.be"]
    start_urls = ["https://www.apcoa.be/locaties/onze-locaties/"]
    rules = [
        Rule(LinkExtractor(allow=r"https://www\.apcoa\.be/parkings-per-stad/[-\w]+/$")),
        Rule(
            LinkExtractor(allow=r"https://www\.apcoa\.be/parkings-per-stad/[-\w]+/[-\w]+/$"),
            callback="parse_sd",
        ),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = item["extras"]["website:nl"] = response.url
        item["extras"]["website:en"] = response.urljoin(
            response.xpath('//a[contains(@href, "/en/parking-per-city/")]/@href').get()
        )
        item["extras"]["website:fr"] = response.urljoin(
            response.xpath('//a[contains(@href, "/fr/parkings-par-ville/")]/@href').get()
        )

        extract_google_position(item, response)
        yield item
