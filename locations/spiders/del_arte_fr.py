from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DelArteFRSpider(SitemapSpider, StructuredDataSpider):
    name = "del_arte_fr"
    item_attributes = {"brand": "Ristorante Del Arte", "brand_wikidata": "Q89208262"}
    sitemap_urls = ["https://www.delarte.fr/media/restaurants-sitemap.xml"]
    sitemap_rules = [(r"/nos-restaurants/.*pizzeria-[^/]+$", "parse_sd")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = item.get("ref").split("/")[-1].split("#")[0]
        item["branch"] = item.pop("name", "").removeprefix("Del Arte Pizzeria - ")
        item["state"] = None
        apply_category(Categories.RESTAURANT, item)

        yield item
