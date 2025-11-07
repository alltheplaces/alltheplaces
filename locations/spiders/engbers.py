from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EngbersSpider(JSONBlobSpider):
    name = "engbers"
    item_attributes = {"brand": "engbers", "brand_wikidata": "Q1290088"}
    EMILIO_ADANI = {"brand": "emilio adani", "brand_wikidata": "Q123022474"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://engbersos-engbers.frontastic.live/frontastic/action/stores/getStoresByLocation",
            data={"type": "storeFinder"},
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature.get("addInfo")
        item["opening_hours"] = OpeningHours()
        opening_hours = feature.get("openingHours", "").replace("<br>", " ").replace("Uhr<br>", ",")
        item["opening_hours"].add_ranges_from_string(opening_hours, days=DAYS_DE)
        if "Emilio Adani" in item.pop("name").title():
            item.update(self.EMILIO_ADANI)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
