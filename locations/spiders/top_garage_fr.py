from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TopGarageFRSpider(SitemapSpider, StructuredDataSpider):
    name = "top_garage_fr"
    item_attributes = {"brand": "Top Garage", "brand_wikidata": "Q117602800"}
    sitemap_urls = ["https://garage.top-garage.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"/details$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
