from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ChurchsChickenUSSpider(SitemapSpider, StructuredDataSpider):
    name = "churchs_chicken_us"
    item_attributes = {"brand": "Church's Chicken", "brand_wikidata": "Q1089932"}
    sitemap_urls = [
        "https://locations.churchs.com/sitemap1.xml",
    ]
    sitemap_rules = [(r"https://locations.churchs.com/[^/]+/[^/]+/[a-z0-9\.A-Z-]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.FAST_FOOD, item)
        yield item
