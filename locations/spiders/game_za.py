from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GameZASpider(JSONBlobSpider):
    name = "game_za"
    item_attributes = {"brand": "Game", "brand_wikidata": "Q126811048"}
    locations_key = "stores"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest("https://www.game.co.za/occ/v2/game/stores?fields=FULL")

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["displayName"].removeprefix("Game ")
        item["name"] = None
        item["state"] = feature["region"]["isocodeShort"]
        item["website"] = None
        item["addr_full"] = item.pop("street_address")

        apply_category(Categories.SHOP_SUPERMARKET, item)

        if oh_data := feature.get("openingHours"):
            item["opening_hours"] = self.parse_opening_hours(oh_data)

        yield item

    def parse_opening_hours(self, opening_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours.get("weekDayOpeningList", []):
            day = rule.get("weekDay")
            if rule.get("closed"):
                oh.set_closed(day)
            elif rule.get("openingTime") and rule.get("closingTime"):
                oh.add_range(
                    day,
                    rule["openingTime"]["formattedHour"],
                    rule["closingTime"]["formattedHour"],
                    "%I:%M %p",
                )
        return oh
