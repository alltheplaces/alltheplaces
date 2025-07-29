from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.costco_us import COSTCO_SHARED_ATTRIBUTES


class CostcoAUSpider(JSONBlobSpider):
    name = "costco_au"
    item_attrributes = COSTCO_SHARED_ATTRIBUTES
    allowed_domains = ["www.costco.com.au"]
    start_urls = ["https://www.costco.com.au/store-finder/search?q=Australia&page=0"]
    locations_key = "data"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["warehouseCode"]
        item["branch"] = feature["name"]
        item.pop("name", None)
        city_state_parts = feature["town"].split(" ")
        if city_state_parts[-1] not in ["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]:
            item["city"] = feature["town"]
        else:
            item["state"] = city_state_parts[-1]
            item["city"] = " ".join(city_state_parts[0:-1])
        item["street_address"] = merge_address_lines([feature["line1"], feature["line2"]])
        item["opening_hours"] = OpeningHours()
        for day_abbrev, day_hours in feature["openings"].items():
            item["opening_hours"].add_range(day_abbrev, *day_hours["individual"].split(" - "), "%I:%M %p")
        item.pop("website", None)
        yield item
