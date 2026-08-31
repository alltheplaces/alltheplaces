from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class MbhBankHUSpider(Spider):
    name = "mbh_bank_hu"
    item_attributes = {"brand": "MBH Bank", "brand_wikidata": "Q124547528"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url="https://www.mbhbank.hu/apps/backend/branch-and-atm")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            category = location["point_category"]

            # "Mobil bankfiók" is one of 14 vehicles serving ~132 towns on weekly 2-4h stops (listed
            # both as category-2 branches and category-0 ATMs); not fixed POIs, so skip them.
            if category == 2 or (location.get("point_name") or "").startswith("Mobil bankfiók"):
                continue

            # Every source key is "point_*"-prefixed; strip it so DictParser can map the standard keys.
            item = DictParser.parse({key.removeprefix("point_"): value for key, value in location.items()})
            item["street_address"] = item.pop("street", None)  # source "street" includes the house number
            item["postcode"] = str(location["point_zip"])  # DictParser maps the numeric zip as an int
            item.pop("phone", None)  # shared call-centre number, not location-specific

            if opening_hours := self.parse_hours(location):
                item["opening_hours"] = opening_hours

            if category == 0:  # ATM
                item.pop("name", None)  # only repeats the address
                apply_category(Categories.ATM, item)
            elif category in (1, 3):  # branch, digital zone
                item["branch"] = item.pop("name", None)
                apply_yes_no(Extras.ATM, item, location.get("point_with_atm") == "Y")
                apply_category(Categories.BANK, item)
            else:
                self.logger.error("Unexpected point_category: {}".format(category))
                continue

            yield item

    def parse_hours(self, location: dict[str, Any]) -> OpeningHours | None:
        hours = OpeningHours()
        try:
            for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
                value = location.get("point_open_{}".format(day))
                if not value or value == "-":
                    continue
                open_time, close_time = value.split("-")
                hours.add_range(DAYS_EN[day.title()], open_time, close_time)
        except (ValueError, AttributeError) as error:
            self.logger.warning("Could not parse hours for {}: {}".format(location.get("point_id"), error))
            return None
        return hours or None
