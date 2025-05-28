from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AsbNZSpider(JSONBlobSpider):
    name = "asb_nz"
    item_attributes = {"brand": "ASB", "brand_wikidata": "Q297214"}
    locations_key = "value"

    def start_requests(self):
        yield JsonRequest(
            "https://api.asb.co.nz/public/v1/locations", headers={"apikey": "l7xx106c7605d7f34e30af0017ca9c69be51"}
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")

        if feature["type"] == "branch":
            apply_category(Categories.BANK, item)

            item["ref"] = feature["branchNumber"]
            apply_yes_no(Extras.WIFI, item, feature["hasFreeWifi"])

            item["opening_hours"] = OpeningHours()
            for rule in feature["openingHours"]:
                item["opening_hours"].add_range(
                    rule["day"], rule["opening"].replace(".", ""), rule["closing"].replace(".", ""), "%I:%M %p"
                )
        elif feature["type"] == "atm":
            apply_category(Categories.ATM, item)

            item["ref"] = feature["atmId"]
            item["extras"]["capacity"] = str(feature["atmCount"])

            if item["branch"].endswith(" Branch"):
                # These are details for the bank, not ATM
                item["branch"] = item["addr_full"] = None

        yield item
