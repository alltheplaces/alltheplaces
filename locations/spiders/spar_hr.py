from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class SparHRSpider(SitemapSpider, StructuredDataSpider):
    name = "spar_hr"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    sitemap_urls = ["https://www.spar.hr/index.sitemap.lokacije-sitemap.xml"]
    sitemap_rules = [("/lokacije/", "parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    time_format = "%H:%M:%S"
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if item["name"].startswith("INTERSPAR hipermarket "):
            item["branch"] = item.pop("name").removeprefix("INTERSPAR hipermarket ")
            item["name"] = "Interspar"
        elif item["name"].startswith("SPAR supermarket "):
            item["branch"] = item.pop("name").removeprefix("SPAR supermarket ")
            item["name"] = "Spar"

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
