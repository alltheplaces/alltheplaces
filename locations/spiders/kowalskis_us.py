from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KowalskisUSSpider(SitemapSpider, StructuredDataSpider):
    name = "kowalskis_us"
    item_attributes = {"brand": "Kowalski's Markets", "brand_wikidata": "Q117231111", "name": "Kowalski's Markets"}
    sitemap_urls = ["https://www.kowalskis.com/sitemap.xml"]
    sitemap_rules = [(r"^https?://www\.kowalskis\.com/locations/[^/]+$", "parse_sd")]
    wanted_types = ["GroceryStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
