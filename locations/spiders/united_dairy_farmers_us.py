from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class UnitedDairyFarmersUSSpider(StructuredDataSpider):
    name = "united_dairy_farmers_us"
    item_attributes = {"brand": "United Dairy Farmers", "brand_wikidata": "Q7887677"}
    start_urls = ["https://www.udfinc.com/our-stores"]
    time_format = "%H:%M:%S"
    wanted_types = ["AutoDealer"]
    search_for_facebook = False
    search_for_twitter = False
    search_for_email = False
    requires_proxy = True
    no_refs = True

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").split("-")[0]
        apply_category(Categories.FUEL_STATION, item)
        yield item
