from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.spiders.five_guys_us import FIVE_GUYS_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysCNSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_cn"
    item_attributes = FIVE_GUYS_SHARED_ATTRIBUTES
    sitemap_urls = ["https://restaurants.fiveguys.cn/sitemap.xml"]
    sitemap_rules = [(r"restaurants\.fiveguys\.cn/en/(?!search$)[^/]+$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]  # Explicitly mention the type to ignore duplicate linked data

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["website"] = response.url
        yield item
