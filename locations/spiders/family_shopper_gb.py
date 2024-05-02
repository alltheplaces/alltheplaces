from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.open_graph_parser import OpenGraphParser


class FamilyShopperGBSpider(SitemapSpider):
    name = "family_shopper_gb"
    item_attributes = {
        "brand": "Family Shopper",
        "brand_wikidata": "Q122731426",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    sitemap_urls = ["https://www.familyshopperstores.co.uk/sitemap.xml"]
    sitemap_rules = [("/our-stores/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = OpenGraphParser.parse(response)
        item["branch"] = (
            item.pop("name").removeprefix("Family Shopper").strip(" -").removeprefix("Family Shopper").strip(" -")
        )
        yield item
