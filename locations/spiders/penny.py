from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import CLOSED_AT, CLOSED_IT, DAYS_AT, DAYS_CZ, DAYS_HU, DAYS_IT, DAYS_RO, OpeningHours
from locations.spiders.penny_de import PennyDESpider

DAYS_BY_COUNTRY = {
    "AT": DAYS_AT,
    "CZ": DAYS_CZ,
    "HU": {**DAYS_HU, "Csüt": "Th"},
    "IT": DAYS_IT,
    "RO": DAYS_RO,
}
CLOSED = CLOSED_AT + CLOSED_IT + ["zavřeno"]


class PennySpider(Spider):
    name = "penny"
    item_attributes = PennyDESpider.item_attributes
    drop_attributes = {"phone"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for country in ["at", "cz", "hu", "it", "ro"]:
            yield JsonRequest(url=f"https://www.penny.{country}/api/stores", cb_kwargs={"cc": country})

    def parse(self, response, **kwargs):
        for store in response.json():
            store["lat"] = store["position"]["lat"]
            store["lon"] = store["position"]["lng"]
            store["street_address"] = store.pop("street")
            store["country"] = kwargs["cc"].upper()

            item = DictParser.parse(store)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                " ".join("{} {}".format(rule["dayOfWeek"], "-".join(rule["times"])) for rule in store["openingTimes"]),
                days=DAYS_BY_COUNTRY[store["country"]],
                closed=CLOSED,
            )
            yield item
