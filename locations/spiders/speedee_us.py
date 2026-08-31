from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SpeedeeUSSpider(SitemapSpider, StructuredDataSpider):
    name = "speedee_us"
    item_attributes = {"brand": "SpeeDee", "brand_wikidata": "Q120537032"}
    sitemap_urls = ["https://www.speedeeoil.com/location-sitemap.xml"]
    sitemap_rules = [(r"/locations/[a-z]{2}/[^/]+/[^/]+/$", "parse_sd")]
    wanted_types = ["AutoRepair"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("name", None)
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
