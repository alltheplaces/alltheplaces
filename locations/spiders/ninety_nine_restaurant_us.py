from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NinetyNineRestaurantUSSpider(SitemapSpider, StructuredDataSpider):
    name = "ninety_nine_restaurant_us"
    item_attributes = {"brand": "Ninety Nine Restaurant & Pub", "brand_wikidata": "Q64358371"}
    sitemap_urls = ["https://99restaurants.com/robots.txt"]
    sitemap_rules = [(r"/locations/[a-z]{2}/[^/]+/[^/]+/$", "parse_sd")]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").split(" – ", 1)[-1]
        apply_category(Categories.RESTAURANT, item)
        yield item
