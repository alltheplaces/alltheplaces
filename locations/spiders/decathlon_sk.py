from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.decathlon_fr import DecathlonFRSpider
from locations.structured_data_spider import StructuredDataSpider


class DecathlonSKSpider(CrawlSpider, StructuredDataSpider):
    name = "decathlon_sk"
    item_attributes = DecathlonFRSpider.item_attributes
    allowed_domains = ["www.decathlon.sk"]
    start_urls = ["https://www.decathlon.sk/content/24-filialen-decathlon"]
    rules = [Rule(LinkExtractor(allow=r"/content/(\d+)-store-"), "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Decathlon ")
        apply_category(Categories.SHOP_SPORTS, item)
        yield item
