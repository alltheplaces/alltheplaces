from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

REMA_1000 = {"brand": "Rema 1000", "brand_wikidata": "Q28459"}


class Rema1000NOSpider(SitemapSpider, StructuredDataSpider):
    name = "rema_1000_no"
    allowed_domains = ["www.rema.no"]
    sitemap_urls = ["https://www.rema.no/sitemap.xml"]
    sitemap_rules = [(r"/butikker/[^/]+/[^/]+/(?:rema-1000|innom)-[^/]+/$", "parse_sd")]
    wanted_types = ["GroceryStore"]
    drop_attributes = {"facebook", "image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        if item["name"].startswith("REMA 1000 "):
            item["branch"] = item.pop("name").removeprefix("REMA 1000 ")
            item.update(REMA_1000)
        elif item["name"].startswith("Innom "):
            item["branch"] = item.pop("name").removeprefix("Innom ")
            item["name"] = "Innom"

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
