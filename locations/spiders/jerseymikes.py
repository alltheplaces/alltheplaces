from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class JerseyMikesSpider(CrawlSpider, StructuredDataSpider):
    name = "jerseymikes"
    item_attributes = {"brand": "Jersey Mike's Subs", "brand_wikidata": "Q6184897"}
    start_urls = [
        "https://www.jerseymikes.com/locations/all",
        "https://www.jerseymikes.ca/locations/all",
    ]
    rules = [
        Rule(LinkExtractor(allow=r"/locations/\w\w")),
        Rule(LinkExtractor(allow=r"/\d+/\w+"), callback="parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)

        yield item
