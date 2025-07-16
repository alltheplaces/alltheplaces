from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class Rue21USSpider(CrawlSpider, StructuredDataSpider):
    name = "rue21_us"
    item_attributes = {"brand": "rue21", "brand_wikidata": "Q7377762"}
    allowed_domains = ["rue21.com"]
    start_urls = ["https://rue21.com/tools/locations/directory"]
    rules = [
        Rule(LinkExtractor(allow=r"^https:\/\/rue21\.com\/tools\/locations\/regions\/[^\/]+$"), follow=True),
        Rule(LinkExtractor(allow=r"^https:\/\/rue21\.com\/tools\/locations\/locations\/[^\/]+$"), callback="parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item.pop("email", None)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
