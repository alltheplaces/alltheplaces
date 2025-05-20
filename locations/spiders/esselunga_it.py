from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.items import Feature, set_closed
from locations.json_blob_spider import JSONBlobSpider


class EsselungaITSpider(JSONBlobSpider):
    name = "esselunga_it"
    item_attributes = {"brand": "Esselunga", "brand_wikidata": "Q1059636"}
    start_urls = ["https://www.esselunga.it/services/istituzionale35/all-stores.json"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["abbrev"]
        item["branch"] = feature["description"] or ""
        if item["branch"].lower().startswith("laesse"):
            item["name"] = "La Esse"
            item["branch"] = item["branch"].split(" ", 1)[1]
        else:
            item["name"] = None
            item["branch"] = item["branch"].removeprefix("Esselunga di ")

        item["opening_hours"] = OpeningHours()
        for day_time in feature.get("openingHours"):
            day = sanitise_day(day_time.get("dayName"), DAYS_IT)
            open_time = day_time.get("opening")
            close_time = day_time.get("closing")
            item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)

        if feature["closed"] is True:
            set_closed(item)
        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
