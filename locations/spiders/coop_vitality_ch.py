from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CoopVitalityCHSpider(JSONBlobSpider):
    name = "coop_vitality_ch"
    item_attributes = {"brand": "Coop Vitality", "brand_wikidata": "Q111725297"}
    allowed_domains = ["www.coopvitality.ch"]
    start_urls = [
        "https://www.coopvitality.ch/jsapi/v2/stores?currentPage=0&lang=de&latitude=46.800663464&longitude=8.222665776&pageSize=1000&pharmacySearchType=&radius=2000000"
    ]
    locations_key = ["stores"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=self.start_urls[0], headers={"Accept-Language": "de"})

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))
        feature["region"] = feature["region"]["isocode"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = "https://www.coopvitality.ch/de/apotheke-finden/" + feature["name"]
        item["ref"] = item["website"]
        item["branch"] = feature["displayName"].removeprefix("Coop Vitality ")
        item.pop("name", None)

        item["opening_hours"] = OpeningHours()
        for day_hours in feature["openingHours"]["openingDays"]:
            if len(day_hours["openingHours"]) == 0:
                item["opening_hours"].set_closed(day_hours["weekDay"].title())
            else:
                for hours_range in day_hours["openingHours"]:
                    item["opening_hours"].add_range(day_hours["weekDay"].title(), *hours_range.split("-", 1), "%H:%M")

        apply_category(Categories.PHARMACY, item)
        yield item
