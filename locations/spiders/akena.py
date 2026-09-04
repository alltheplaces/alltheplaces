from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AkenaSpider(SitemapSpider, StructuredDataSpider):
    name = "akena"
    item_attributes = {"brand": "Akena", "brand_wikidata": "Q107089744"}
    sitemap_urls = ["https://www.akena.com/sitemap.xml"]
    sitemap_rules = [(r"^https://www\.akena\.com/agences/[^/]+/?$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image", "facebook"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("phone") == "0 800 031 500":
            item["phone"] = None
        item["branch"] = item.pop("name").removeprefix("AKENA ")

        apply_category(Categories.CRAFT_CARPENTER, item)
        yield item
