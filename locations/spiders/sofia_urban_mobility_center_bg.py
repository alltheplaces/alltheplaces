from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SofiaUrbanMobilityCenterBGSpider(JSONBlobSpider):
    name = "sofia_urban_mobility_center_bg"
    item_attributes = {
        "brand": "Център за градска мобилност",
        "brand_wikidata": "Q7553668",
    }
    start_urls = ["https://webportal.sofiatraffic.bg/sales-points"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("location"))
        names = feature.pop("name")
        feature["name"] = names["bg"]
        feature["name_en"] = names.get("en")

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        if feature.get("name_en"):
            item["extras"]["branch:en"] = feature["name_en"]

        hours = feature.get("workingHours") or {}
        item["opening_hours"] = OpeningHours()
        if hours.get("weekday"):
            item["opening_hours"].add_days_range(DAYS_WEEKDAY, *hours["weekday"].split("-"))
        if hours.get("saturday"):
            item["opening_hours"].add_range("Sa", *hours["saturday"].split("-"))
        if hours.get("sunday"):
            item["opening_hours"].add_range("Su", *hours["sunday"].split("-"))

        apply_category(Categories.SHOP_TICKET, item)
        yield item
