from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SmashburgerSpider(CrawlSpider, StructuredDataSpider):
    name = "smashburger"
    item_attributes = {"brand": "Smashburger", "brand_wikidata": "Q17061332"}
    allowed_domains = ["smashburger.com"]
    start_urls = ["https://smashburger.com/locations"]
    rules = [
        Rule(LinkExtractor(allow=r"^https://smashburger\.com/locations/\w\w(?:/\w\w)?(?:/[^/]+)?$")),
        Rule(LinkExtractor(allow=r"^https://smashburger\.com/locations/\w\w/\w\w/[^/]+/[^/]+$"), callback="parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["website"] = response.url
        item.pop("facebook")
        item.pop("twitter")
        yield item
