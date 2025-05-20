from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HammerDESpider(JSONBlobSpider):
    name = "hammer_de"
    item_attributes = {"brand": "Hammer", "brand_wikidata": "Q52159668"}
    start_urls = ["https://www.hammer-zuhause.de/maerkte/hammer"]
    locations_key = "results"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("id")
        item["name"] = feature["description"]
        item["website"] = f"https://www.hammer-zuhause.de/maerkte/storeDetail?storeCode={item['ref']}"
        item["opening_hours"] = OpeningHours()
        for hour in feature["openingHours"]["weekDayOpeningList"]:
            item["opening_hours"].add_range(
                DAYS_DE[hour["weekDay"]], hour["openingTime"]["formattedHour"], hour["closingTime"]["formattedHour"]
            )
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
