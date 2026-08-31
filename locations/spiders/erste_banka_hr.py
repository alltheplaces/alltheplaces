import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature


class ErsteBankaHRSpider(Spider):
    name = "erste_banka_hr"
    item_attributes = {"brand": "Erste Bank", "brand_wikidata": "Q696867"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url="https://local.erstebank.hr/api/v1/branches",
            cb_kwargs={"location_type": "branch"},
        )
        yield JsonRequest(
            url="https://local.erstebank.hr/api/v1/atms",
            cb_kwargs={"location_type": "atm"},
        )

    def parse(self, response: Response, location_type: str, **kwargs: Any) -> Any:
        for location in response.json()["items"]:
            item = self.parse_location(location)

            if location_type == "branch":
                if branch := item.pop("name", None):
                    item["branch"] = re.sub(
                        r"^(?:Poslovnica|Filijala|Savjetodavni centar|Stambeni centar)\s+", "", branch
                    ).strip()
                apply_category(Categories.BANK, item)
            elif location_type == "atm":
                item.pop("name", None)
                if (branch := location.get("location", "").strip()) and branch.upper() not in {
                    "BANKA",
                    "KIOSK",
                    "POSLOVNI PROSTOR",
                    "SAMOSTOJEĆI KIOSK",
                    "SAMOUSLUŽNA ZONA",
                    "STAMBENA ZGRADA",
                }:
                    item["branch"] = branch
                apply_yes_no(
                    Extras.CASH_IN,
                    item,
                    location.get("features", {}).get("atmDeposit") in (True, "true", "True", "TRUE"),
                    False,
                )
                apply_category(Categories.ATM, item)
            else:
                self.logger.error("Unexpected location type: {}".format(location_type))
                continue

            yield item

    @staticmethod
    def parse_location(location: dict[str, Any]) -> Feature:
        item = DictParser.parse(location)

        if position := location.get("position", {}):
            item["lat"] = position.get("lat")
            item["lon"] = position.get("lng")

        if address := location.get("address", {}):
            item["street_address"] = address.get("street")
            item["city"] = address.get("city")
            item["postcode"] = str(postcode) if (postcode := address.get("postcode")) else None

        return item
