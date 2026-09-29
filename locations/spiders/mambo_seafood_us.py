from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MamboSeafoodUSSpider(SitemapSpider, StructuredDataSpider):
    name = "mambo_seafood_us"
    item_attributes = {"brand": "Mambo Seafood"}
    sitemap_urls = ["https://locations.mamboseafood.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/tx/[^/]+/[^/]+$", "parse_sd")]
    search_for_amenity_features = False
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url
        item["name"] = None
        item["branch"] = (
            response.xpath("normalize-space(//h1)")
            .get("")
            .removeprefix("Mambo Seafood - ")
            .removeprefix("Mambo Seafood ")
        )
        item["website"] = response.url
        apply_category(Categories.RESTAURANT, item)
        yield item
