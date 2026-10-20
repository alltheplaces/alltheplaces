from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class JdSportsITSpider(CrawlSpider, StructuredDataSpider, PlaywrightSpider):
    name = "jd_sports_it"
    item_attributes = {"brand": "JD Sports", "brand_wikidata": "Q6108019"}
    start_urls = ["https://www.jdsports.it/store-locator/all-stores/"]
    rules = [Rule(LinkExtractor(allow="store-locator/", deny="-soon"), callback="parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
