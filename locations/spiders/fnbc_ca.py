from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class FnbcCASpider(Spider):
    name = "fnbc_ca"
    FNBC = {"brand": "First Nations Bank of Canada", "brand_wikidata": "Q1419511"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api.forge.central1.cc/find-branch-atm-service/v1/places?latitude=58.55148693137242&longitude=-94.06979&radius=4000&type=all&dedupeAtms=true",
            headers={"c1-tid": "sk_fnbc"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location_type in ["branches", "atms"]:
            locations = response.json()[location_type]
            for location in locations:
                location.update(location.pop("details", {}))
                item = DictParser.parse(location)
                item["street_address"] = merge_address_lines(location["address"].get("line"))

                if location.get("type") == "branch":
                    item["branch"] = item.pop("name")
                    phone_details = location["contacts"][0]["phone"]
                    item["phone"] = (
                        str(phone_details["areacode"]) + phone_details["phone"]
                        if phone_details.get("areacode")
                        else phone_details["phone"]
                    )
                    item["opening_hours"] = self.parse_opening_hours(location["operationHours"]["regularHours"][0])
                    item["website"] = f'https://www.fnbc.ca/find-a-location?branchId={location["id"]}'
                    item.update(self.FNBC)
                    item["name"] = item["brand"]
                    apply_category(Categories.BANK, item)
                    apply_yes_no(Extras.ATM, item, "ATM" in location["info"]["service"])

                elif location.get("type") == "atm":
                    if item["name"] == self.FNBC["brand"]:
                        item.update(self.FNBC)
                    else:
                        # ATMs of other brands/operators
                        pass
                    apply_category(Categories.ATM, item)

                yield item

    def parse_opening_hours(self, opening_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            if rule := opening_hours.get(day.lower()):
                if rule.get("isOpen"):
                    oh.add_range(day, rule["openTime"], rule["closeTime"], "%I:%M %p")
                else:
                    oh.set_closed(day)
        return oh
