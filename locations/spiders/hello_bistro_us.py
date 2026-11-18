from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HelloBistroUSSpider(SitemapSpider, StructuredDataSpider):
    name = "hello_bistro_us"
    item_attributes = {"brand": "Hello Bistro"}
    allowed_domains = ["hellobistro.com"]
    sitemap_urls = ["https://locations.hellobistro.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z]{2}-[-\w]+-(\d+)/?$", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = (
            response.xpath('//*[@id="RSEOStoreLocatorContent"]//p/text()').get("").split("(", 1)[-1].strip(")")
        )
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "salad;burger"
        yield item
