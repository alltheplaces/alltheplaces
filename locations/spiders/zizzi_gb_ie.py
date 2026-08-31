from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ZizziGBIESpider(SitemapSpider, StructuredDataSpider):
    name = "zizzi_gb_ie"
    item_attributes = {"brand": "Zizzi", "brand_wikidata": "Q8072944"}
    sitemap_urls = ["https://www.zizzi.co.uk/sitemap.xml"]
    sitemap_rules = [
        (r"/italian-restaurants/((?!.*/(?:poi|offers|news|menus)(?:/|$))[^/]+/[^/]+(?:/[^/]+)?)$", "parse")
    ]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # Each page carries two Restaurant blocks, skip the "#restaurant" duplicate.
        if ld_data.get("@id", "").endswith("#restaurant"):
            return

        item["branch"] = item.pop("name")

        # The site reports every location as GB, so correct Republic of Ireland.
        if response.url.split("/italian-restaurants/", 1)[1].split("/", 1)[0] == "ireland":
            item["country"] = "IE"
            item.pop("state", None)

        apply_category(Categories.RESTAURANT, item)

        yield item
