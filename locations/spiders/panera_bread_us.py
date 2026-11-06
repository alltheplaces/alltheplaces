import re
from typing import Any, AsyncIterator

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


def slugify(s):
    return re.sub(r"\W+", "-", s).lower()


class PaneraBreadUSSpider(Spider):
    name = "panera_bread_us"
    item_attributes = {"brand": "Panera Bread", "brand_wikidata": "Q7130852"}
    headers = {"Referer": "https://www.panerabread.com/"}

    async def start(self) -> AsyncIterator[Request]:
        for state in GeonamesCache().get_us_states():
            yield Request(
                f"https://www-api.panerabread.com/www-api/public/cafe/location/{state.lower()}",
                headers=self.headers,
            )

    def parse(self, response):
        for city in response.json():
            for cafe in city["cafes"]:
                item = DictParser.parse(cafe)
                item["branch"] = item.pop("name")
                item["ref"] = cafe["cafeId"]
                item["street_address"] = item.pop("street")
                item["website"] = (
                    f"https://www.panerabread.com/content/panerabread_com/en-us/cafe/locations/{slugify(cafe['state'])}/{slugify(cafe['city'])}/{slugify(cafe['streetName'])}"
                )

                features = cafe["searchFlags"]
                apply_yes_no(Extras.INDOOR_SEATING, item, features["hasDineIn"])
                apply_yes_no(Extras.DELIVERY, item, features["hasDelivery"])
                apply_yes_no(Extras.TAKEAWAY, item, features["hasPickup"])
                apply_yes_no(Extras.DRIVE_THROUGH, item, features["hasDriveThru"])

                apply_category(Categories.FAST_FOOD, item)

                yield Request(
                    f"https://www-api.panerabread.com/www-api/public/cafe/details/{cafe['cafeId']}",
                    headers=self.headers,
                    callback=self.parse_details,
                    cb_kwargs={"item": item},
                )

    def parse_details(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        if cafes := response.json().get("cafeList"):
            item["opening_hours"] = OpeningHours()
            for day, ranges in cafes[0]["cafeHours"]["dinein"]["hours"].items():
                for hours in ranges:
                    item["opening_hours"].add_range(day, hours["open"], hours["close"])
        yield item
