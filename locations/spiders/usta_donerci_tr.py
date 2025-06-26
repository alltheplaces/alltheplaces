from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class UstaDonerciTRSpider(JSONBlobSpider):
    name = "usta_donerci_tr"
    item_attributes = {"brand": "Usta Dönerci", "brand_wikidata": "Q126723224"}
    start_urls = ["https://www.ustadonerci.com/locations/"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("data"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["restaurantId"]
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("addr_full")
        item["extras"]["addr:district"] = item.pop("state")

        item["opening_hours"] = OpeningHours()
        for day in DAYS:
            item["opening_hours"].add_range(day, feature["openingTime"], feature["closingTime"])

        apply_category(Categories.FAST_FOOD, item)
        yield item
