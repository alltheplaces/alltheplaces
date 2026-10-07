from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class CoinhubUSSpider(StorepointSpider):
    name = "coinhub_us"
    item_attributes = {"brand": "Coinhub", "brand_wikidata": "Q126195855"}
    key = "162cb508a25fa2"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=f"https://api.storepoint.co/v2/{self.key}/locations/country?country_code=US")

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        if " - Inside " in item["name"]:
            item["located_in"] = item["name"].split(" - Inside ", 1)[1]
        for day in DAYS_FULL:
            if (location.get(day.lower()) or "").replace(" ", "").upper() == "12:00AM-12:00AM":
                item["opening_hours"].add_range(day, "00:00", "24:00")
        item.pop("name", None)
        item.pop("phone", None)
        item.pop("email", None)
        apply_category(Categories.ATM, item)
        item["extras"]["currency:XBT"] = "yes"
        item["extras"]["currency:USD"] = "yes"
        item["extras"]["cash_in"] = "yes"
        item["extras"]["cash_out"] = "no"
        yield item
