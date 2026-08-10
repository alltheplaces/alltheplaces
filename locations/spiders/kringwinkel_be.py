from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KringwinkelBESpider(JSONBlobSpider):
    name = "kringwinkel_be"
    item_attributes = {"name": "Kringwinkel", "brand": "De Kringwinkel", "brand_wikidata": "Q55935433"}
    start_urls = ["https://www.kringwinkel.be/json/winkels.json"]

    def pre_process_data(self, feature: dict) -> None:
        postalcode = feature.pop("postalcode", {}) or {}
        feature["postcode"] = postalcode.get("postalcode")
        feature["city"] = postalcode.get("city")
        feature.pop("phone", None)
        feature.pop("email", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Kringwinkel ")
        item["street_address"] = item.pop("addr_full")
        item["website"] = "https://www.kringwinkel.be/winkels/" + feature["slug"]

        item["opening_hours"] = OpeningHours()
        for schedule in feature.get("opening_hours") or []:
            if schedule.get("type") != "Winkel":
                continue
            for day, day_name in zip(DAYS, DAYS_FULL):
                if not (value := schedule.get(day_name.lower())):
                    item["opening_hours"].set_closed(day)
                    continue
                for part in value.split("|"):
                    start, _, end = part.partition("-")
                    if (start := start.strip()) and (end := end.strip()) and start < end:
                        item["opening_hours"].add_range(day, start, end)

        apply_yes_no(Extras.WHEELCHAIR, item, feature.get("is_rolstoeltoegankelijk"))
        apply_yes_no(Extras.TOILETS, item, feature.get("is_wc"))
        apply_yes_no(Extras.WIFI, item, feature.get("is_wifi"))
        apply_yes_no(Extras.DOG, item, feature.get("is_honden_toegelaten"))

        apply_category(Categories.SHOP_SECOND_HAND, item)
        yield item
