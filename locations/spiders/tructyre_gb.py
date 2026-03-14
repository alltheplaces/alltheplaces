from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TructyreGBSpider(SitemapSpider, StructuredDataSpider):
    name = "tructyre_gb"
    item_attributes = {
        "name": "Tructyre",
        "brand": "Tructyre",
        "brand_wikidata": "Q109383654",
    }
    sitemap_urls = ["https://www.tructyre.co.uk/robots.txt"]
    sitemap_rules = [(r"https://www.tructyre.co.uk/locations/[^/]+$", "parse_sd")]
    wanted_types = ["TireShop"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        item["image"] = None
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
