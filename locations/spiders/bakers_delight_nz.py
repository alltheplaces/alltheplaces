from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BakersDelightNZSpider(JSONBlobSpider):
    name = "bakers_delight_nz"
    item_attributes = {"brand": "Bakers Delight", "brand_wikidata": "Q4849261"}
    allowed_domains = ["bakersdelight.co.nz"]
    start_urls = ["https://bakersdelight.co.nz/wp-content/uploads/ssf-wp-uploads/ssf-data.json"]
    locations_key = "item"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["location"]
        hours_string = " ".join(
            Selector(text=feature["operatingHours"])
            .xpath('//table[not(contains(@class, "wpsl-opening-hours--special"))]//text()')
            .getall()
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        item["image"] = feature["storeimage"]
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
