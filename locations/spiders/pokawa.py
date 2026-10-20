import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PokawaSpider(SitemapSpider, StructuredDataSpider):
    name = "pokawa"
    item_attributes = {"brand": "Pokawa", "brand_wikidata": "Q123018553"}
    sitemap_urls = ["https://restaurants.pokawa.com/sitemap.xml"]
    sitemap_rules = [(r"https://restaurants\.pokawa\.com/[^/]+/[^/]+/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        if match := re.search(r'lat\\":(-?\d+\.\d+).{0,40}?lng\\":(-?\d+\.\d+)', response.text):
            item["lat"], item["lon"] = match.groups()
        if match := re.search(r'shortName\\":\\"([^"\\]+)', response.text):
            item.pop("name", None)
            item["branch"] = match.group(1)
        apply_category(Categories.FAST_FOOD, item)
        yield item
