from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CentraGBSpider(JSONBlobSpider):
    name = "centra_gb"
    item_attributes = {"brand": "Centra", "brand_wikidata": "Q747678"}
    start_urls = ["https://centra.co.uk/wp-json/app/get_stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            item["opening_hours"].add_range(
                day,
                feature["openingHours"][day.lower()]["open"],
                feature["openingHours"][day.lower()]["closed"],
                time_format="%I:%M%p",
            )
        apply_category(Categories.SHOP_CONVENIENCE, item)
        apply_yes_no("sells:alcohol", item, feature["offlicence"])
        if feature["forecourt"] == "Yes":
            apply_category(Categories.FUEL_STATION, item)
        yield item
