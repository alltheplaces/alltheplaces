from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ToomBaumarktDESpider(JSONBlobSpider):
    name = "toom_baumarkt_de"
    item_attributes = {"brand": "toom Baumarkt", "brand_wikidata": "Q2442970"}
    start_urls = ["https://api.toom.de/public/api/markets"]
    locations_key = "markets"

    def pre_process_data(self, location: dict) -> None:
        location.update(location.pop("address"))
        location.pop("country", None)

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("street")
        item["website"] = "https://toom.de/" + location["link"]

        item["opening_hours"] = OpeningHours()
        for rule in location["openingTimes"]:
            value = rule["value"]
            if value.get("opening") and value.get("closing"):
                item["opening_hours"].add_range(DAYS[value["dayofweek"]], value["opening"], value["closing"])

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
