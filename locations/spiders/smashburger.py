from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class SmashburgerSpider(CrawlSpider, StructuredDataSpider):
    name = "smashburger"
    item_attributes = {"brand": "Smashburger", "brand_wikidata": "Q17061332"}
    allowed_domains = ["smashburger.com"]
    start_urls = ["https://smashburger.com/locations/index.html"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/smashburger\.com\/locations\/[a-z]{2}\/[a-z]{2}(?:\/(?:[^/]+\/?))?$"),
            follow=True,
        ),
        Rule(
            LinkExtractor(allow=r"^https:\/\/smashburger\.com\/locations\/[a-z]{2}\/[a-z]{2}\/[^/]+\/.+"),
            callback="parse_sd",
            follow=False,
        ),
    ]

    def post_process_item(self, item, response, ld_data):
        item["website"] = response.url
        item.pop("facebook")
        item.pop("twitter")
        yield item
