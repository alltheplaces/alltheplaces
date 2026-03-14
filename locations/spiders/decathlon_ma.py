from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.decathlon_fr import DecathlonFRSpider
from locations.structured_data_spider import StructuredDataSpider


class DecathlonMASpider(CrawlSpider, StructuredDataSpider):
    name = "decathlon_ma"
    item_attributes = DecathlonFRSpider.item_attributes
    allowed_domains = ["www.decathlon.ma"]
    start_urls = ["https://www.decathlon.ma/content/154-filialen-decathlon"]
    rules = [Rule(LinkExtractor(allow=r"/content/(\d+)-store-"), "parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def pre_process_data(self, ld_data: dict, **kwargs):
        for rule in ld_data.get("openingHoursSpecification", []):
            for key in ["opens", "closes"]:
                rule[key] = rule.get(key, "").replace("H", ":")

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("DECATHLON ")
        apply_category(Categories.SHOP_SPORTS, item)
        yield item
