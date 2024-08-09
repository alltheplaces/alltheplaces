import re

from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.algolia import AlgoliaSpider


class JbHifiAUSpider(AlgoliaSpider):
    name = "jb_hifi_au"
    item_attributes = {"brand": "JB Hi-Fi", "brand_wikidata": "Q3310113"}
    api_key = "a0c0108d737ad5ab54a0e2da900bf040"
    app_id = "VTVKM5URPX"
    index_name = "shopify_store_locations"

    def process_trading_hours(self, store_hours):
        opening_hours = OpeningHours()
        for day in store_hours:
            if "NULL" not in day.get("OpeningTime", "NULL") and "NULL" not in day.get("ClosingTime", "NULL"):
                opening_hours.add_range(
                    DAYS_3_LETTERS_FROM_SUNDAY[day["DayOfWeek"]], day["OpeningTime"], day["ClosingTime"]
                )

        return opening_hours.as_opening_hours()

    def parse_item(self, item, location):
        if location.get("displayOnWeb") != "p":
            return

        if location["locationType"] == 2:
            item["brand"] = item["name"] = "JB Hi-Fi Home"
        else:
            del item["name"]

        item["ref"] = location["shopId"]
        item["branch"] = location["storeName"]
        item["street_address"] = clean_address(
            [
                location["storeAddress"]["Line1"],
                location["storeAddress"].get("Line2"),
                location["storeAddress"].get("Line3"),
            ]
        )
        item["lat"] = location["_geoloc"]["lat"]
        item["lon"] = location["_geoloc"]["lng"]
        item["opening_hours"] = self.process_trading_hours(location["normalTradingHours"])

        slug = re.sub(r"\W+", "-", location["storeName"]).lower()
        item["website"] = f"https://www.jbhifi.com.au/pages/{slug}"

        yield item
