from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.algolia import AlgoliaSpider


class JbhifiSpider(AlgoliaSpider):
    name = "jbhifi"
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
        item["ref"] = location["shopId"]
        item["name"] = location["storeName"]
        item["street_address"] = clean_address(
            [
                location["storeAddress"]["Line1"],
                location["storeAddress"].get("Line2"),
                location["storeAddress"].get("Line3"),
            ]
        )
        item["city"] = location["storeAddress"]["Suburb"]
        item["state"] = location["storeAddress"].get("State")
        item["postcode"] = location["storeAddress"]["Postcode"]
        item["country"] = "AU"
        item["lat"] = location["_geoloc"]["lat"]
        item["lon"] = location["_geoloc"]["lng"]
        item["phone"] = location["phone"]
        item["opening_hours"] = self.process_trading_hours(location["normalTradingHours"])

        yield item
