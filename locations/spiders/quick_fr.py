from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class QuickFRSpider(JSONBlobSpider):
    name = "quick_fr"
    item_attributes = {"brand": "Quick", "brand_wikidata": "Q286494"}
    allowed_domains = ["www.quick.fr"]
    start_urls = ["https://www.quick.fr/restaurants"]

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        for d in chompjs.parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]//text()').get())["props"][
            "pageProps"
        ]["dehydratedState"]["queries"]:
            if "restaurants" in d["queryKey"]:
                return d["state"]["data"]

    def pre_process_data(self, feature: dict):
        feature.update(feature["attributes"])

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", "")
        item["website"] = "https://www.quick.fr/restaurants/" + location["slug"]

        item["opening_hours"] = OpeningHours()
        for d in DAYS_FULL:
            if hours := location.get("dining{}".format(d)):
                item["opening_hours"].add_ranges_from_string(d + " " + hours)

        apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(Extras.WIFI, item, location.get("wifi", "") == "Oui")
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, location.get("changingTable", "") == "Oui")
        apply_yes_no(Extras.AIR_CONDITIONING, item, location.get("airConditioning", "") == "Oui")
        apply_yes_no(Extras.OUTDOOR_SEATING, item, location.get("terrace", "") == "Oui")
        apply_yes_no(Extras.DRIVE_THROUGH, item, location.get("drive", "") == "Oui")
        apply_yes_no(Extras.TAKEAWAY, item, location.get("takeaway", "") == "Oui")
        apply_yes_no(Extras.WHEELCHAIR, item, location.get("pmr", "") == "Oui")

        yield item
