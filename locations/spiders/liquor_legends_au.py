from json import loads
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LiquorLegendsAUSpider(JSONBlobSpider):
    name = "liquor_legends_au"
    item_attributes = {"brand": "Liquor Legends", "brand_wikidata": "Q126175687"}
    allowed_domains = ["rewardsapi.liquorlegends.com.au"]
    start_urls = ["https://rewardsapi.liquorlegends.com.au/api/v1/venue/geo-json"]
    locations_key = "features"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))
        feature.update(loads(feature.pop("location_data"))["store_details"])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        item["branch"] = item.pop("name").removeprefix("Liquor Legends ")
        item["street_address"] = item.pop("addr_full", None)
        item["website"] = "https://liquorlegends.com.au/?outlet={}".format(item["ref"])
        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in loads(feature["opening_hours"]).items():
            if day_name not in DAYS_FULL:
                continue
            if not day_hours["open"] or not day_hours["close"]:
                item["opening_hours"].set_closed(day_name)
                continue
            item["opening_hours"].add_range(DAYS_EN[day_name], day_hours["open"], day_hours["close"], "%I:%M%p")
        apply_category(Categories.SHOP_ALCOHOL, item)
        yield item
