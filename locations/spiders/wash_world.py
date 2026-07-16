from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WashWorldSpider(SitemapSpider, StructuredDataSpider):
    name = "wash_world"
    item_attributes = {"brand": "Wash World", "brand_wikidata": "Q130249954"}
    sitemap_urls = [
        "https://washworld.dk/pages-sitemap.xml",
        "https://washworld.se/pages-sitemap.xml",
        "https://washworld.de/pages-sitemap.xml",
        "https://washworld.no/pages-sitemap.xml",
    ]
    sitemap_rules = [
        ("/find-wash-world-vaskehal/", "parse_sd"),
        ("/hitta-biltvatt/", "parse_sd"),
        ("/waschanlagen/", "parse_sd"),
        ("/finn-vaskehall/", "parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Wash World ", "")
        item["image"] = None
        item["addr_full"] = item.pop("street_address")
        apply_category(Categories.CAR_WASH, item)
        yield item
