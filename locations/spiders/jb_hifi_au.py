import re
from typing import Iterable

from scrapy.http import Response

from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.algolia import AlgoliaSpider


class JbHifiAUSpider(AlgoliaSpider):
    name = "jb_hifi_au"
    item_attributes = {"brand": "JB Hi-Fi", "brand_wikidata": "Q3310113"}
    api_key = "a0c0108d737ad5ab54a0e2da900bf040"
    app_id = "VTVKM5URPX"
    index_name = "shopify_store_locations"

    def extract_opening_hours(self, store_hours: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in store_hours:
            if "NULL" not in day.get("OpeningTime", "NULL") and "NULL" not in day.get("ClosingTime", "NULL"):
                opening_hours.add_range(
                    DAYS_3_LETTERS_FROM_SUNDAY[day["DayOfWeek"]], day["OpeningTime"], day["ClosingTime"]
                )

        return opening_hours

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("displayOnWeb") != "p":
            return

        if feature["locationType"] == 2:
            item["brand"] = item["name"] = "JB Hi-Fi Home"
        else:
            del item["name"]

        item["ref"] = feature["shopId"]
        item["branch"] = feature["storeName"]
        item["street_address"] = clean_address(
            [
                feature["storeAddress"]["Line1"],
                feature["storeAddress"].get("Line2"),
                feature["storeAddress"].get("Line3"),
            ]
        )
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["opening_hours"] = self.extract_opening_hours(feature["normalTradingHours"])

        slug = re.sub(r"\W+", "-", feature["storeName"]).lower()
        item["website"] = f"https://www.jbhifi.com.au/pages/{slug}"

        yield item
