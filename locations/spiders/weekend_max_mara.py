from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WeekendMaxMaraSpider(SitemapSpider, StructuredDataSpider):
    name = "weekend_max_mara"
    item_attributes = {"brand": "Weekend Max Mara", "brand_wikidata": "Q136159038"}
    sitemap_urls = ["https://store.weekendmaxmara.com/robots.txt"]
    sitemap_rules = [(r"https://store\.weekendmaxmara\.com/en/[^/]+/[^/]+/weekend-max-mara-[^/]+$", "parse")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Weekend Max Mara ")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
