from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class FuzzysTacoShopUSSpider(CrawlSpider, StructuredDataSpider):
    name = "fuzzys_taco_shop_us"
    item_attributes = {"brand": "Fuzzy's Taco Shop", "brand_wikidata": "Q85762348"}
    allowed_domains = ["fuzzystacoshop.com"]
    start_urls = ["https://fuzzystacoshop.com/locations/list/"]
    rules = [
        Rule(LinkExtractor(allow=r"https:\/\/fuzzystacoshop\.com\/locations\/list\/.+")),
        Rule(
            LinkExtractor(allow=r"https:\/\/fuzzystacoshop\.com\/locations\/(?!list\/).+"),
            callback="parse_sd",
            follow=False,
        ),
    ]

    def post_process_item(self, item, response, ld_data):
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].from_linked_data(ld_data, time_format="%H:%M:%S")
        yield item
