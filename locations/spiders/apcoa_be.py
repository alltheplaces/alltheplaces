from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class ApcoaSpider(CrawlSpider, StructuredDataSpider):
    name = "apcoa_be"
    item_attributes = {"brand": "APCOA Parking", "brand_wikidata": "Q296108"}
    allowed_domains = ["www.apcoa.be"]
    start_urls = ["https://www.apcoa.be"]
    rules = [
        Rule(LinkExtractor(allow=r"https://www\.apcoa\.be/parkings-per-stad/[-\w]+/$")),
        Rule(
            LinkExtractor(allow=r"https://www\.apcoa\.be/parkings-per-stad/[-\w]+/[-\w]+/$"),
            callback="parse_sd",
        ),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)
        yield item
