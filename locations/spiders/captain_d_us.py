from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class CaptainDUSSpider(Where2GetItSpider):
    name = "captain_d_us"
    item_attributes = {"brand": "Captain D's", "brand_wikidata": "Q5036616"}
    api_brand_name = "captainseafoodsites"
    api_key = "596EECC8-DFC6-11EE-AA1D-2E122CD69500"
    custom_settings = {
        "DOWNLOAD_WARNSIZE": 67108864,  # 64 MiB needed as results are >32 MiB
    }

    def parse_item(self, item: Feature, location: dict):
        if not location.get("latitude"):
            # There is at least one "corporate" feature which is not a real
            # feature with physical address. Ignore such "feature".
            return
        if location.get("name") and "COMING SOON" in location["name"].upper():
            return

        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]
        item["branch"] = item.pop("name", None)

        item["opening_hours"] = OpeningHours()
        for day_name in DAYS_FULL:
            if not location.get("{}_open".format(day_name.lower())):
                item["opening_hours"].set_closed(DAYS_EN[day_name])
            else:
                item["opening_hours"].add_range(
                    DAYS_EN[day_name],
                    location["{}_open".format(day_name.lower())],
                    location["{}_close".format(day_name.lower())],
                )

        apply_category(Categories.FAST_FOOD, item)
        yield item
