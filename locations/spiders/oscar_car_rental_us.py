from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class OscarCarRentalUSSpider(SitemapSpider, StructuredDataSpider):
    name = "oscar_car_rental_us"
    item_attributes = {"brand": "Oscar Car Rental", "brand_wikidata": "Q127731404"}
    sitemap_urls = ["https://driveoscar.com/robots.txt"]
    sitemap_rules = [(r"https://driveoscar.com/locations/([^/]+)$", "parse")]
    wanted_types = ["AutoRental"]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Oscar Car Rental ")
        item["image"] = None
        apply_category(Categories.CAR_RENTAL, item)
        yield item
