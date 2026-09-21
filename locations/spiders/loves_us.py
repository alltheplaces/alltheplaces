from typing import Any, AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class LovesUSSpider(scrapy.Spider):
    name = "loves_us"
    SPEEDCO = {"brand": "Speedco", "brand_wikidata": "Q112455073"}
    item_attributes = {"brand": "Love's", "brand_wikidata": "Q1872496"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        # A prior "fetch_all_stores" GET endpoint (used by an older version of
        # this site) has been retired following a site redesign; the store
        # locator now POSTs to this endpoint with an empty body for the full list.
        yield JsonRequest(url="https://www.loves.com/api/fetch_stores", data={}, method="POST")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]:
            if store["isHotel"] is True:
                continue  # ChoiceHotelsSpider
            if not (store["isLoveStore"] or store["isCountryStore"] or store["isSpeedco"]):
                # Locations that are neither Love's nor Speedco branded, e.g. a
                # contracted turnpike service plaza operated but not branded by Love's.
                continue

            item = DictParser.parse(store)
            item["name"] = None
            item["branch"] = store.get("preferredName")
            item["ref"] = store.get("number")
            item["website"] = "https://www.loves.com/locations/{}".format(store["number"])

            is_24_hours = any(
                a.get("smaFieldName") == "24hourservice" and str(a.get("fieldValue")).lower() == "true"
                for a in store.get("mappedCustomFields", {}).get("additionalAmenities", [])
            )
            if is_24_hours:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")

            if store["isSpeedco"]:
                item.update(self.SPEEDCO)
                apply_category(Categories.SHOP_TRUCK_REPAIR, item)
            elif store["isCountryStore"]:
                apply_category(Categories.FUEL_STATION, item)
            else:
                apply_category(Categories.HIGHWAY_SERVICES, item)
            yield item
