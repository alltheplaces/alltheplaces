import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class PrivrednaBankaZagrebHRSpider(Spider):
    name = "privredna_banka_zagreb_hr"
    item_attributes = {"brand": "Privredna banka Zagreb", "brand_wikidata": "Q7246343"}

    async def start(self) -> AsyncIterator[Any]:
        for location_type in ["BRANCH", "ATM"]:
            yield JsonRequest(
                url=(
                    "https://www.pbz.hr/digitalServicesServlet/?operation=fetchMarkers&headers=lbsHeader"
                    "&endpointName=fetchMarkers&bank=PBZ&locale=en"
                ),
                data={"locationType": location_type},
                cb_kwargs={"location_type": location_type},
            )

    def parse(self, response: Response, location_type: str, **kwargs: Any) -> Any:
        for location in response.json().get("locationDetails", []):
            item = self.parse_location(location)

            if location_type == "BRANCH":
                apply_category(Categories.BANK, item)
            elif location_type == "ATM":
                apply_category(Categories.ATM, item)
            else:
                self.logger.error("Unexpected location type: {}".format(location_type))
                continue

            yield item

    def parse_location(self, location: dict[str, Any]) -> Feature:
        item = DictParser.parse(location)

        if position := location.get("locationPosition", {}):
            item["lat"] = position.get("lat")
            item["lon"] = position.get("lon")

        if branch := item.pop("name", None):
            item["branch"] = re.sub(
                r"\s+\([^)]*\)$", "", branch.removeprefix("PBZ ").removeprefix("POSLOVNICA ")
            ).strip()

        # PBZ provides address parts only as a flat fullAddress string.
        if match := re.match(
            r"(?P<street_address>.+)\s+(?P<postcode>\d{5})\s+(?P<city>.+?)(?:\s+Hrvatska)?\s*$",
            location.get("fullAddress", ""),
            flags=re.IGNORECASE,
        ):
            item["street_address"] = match.group("street_address")
            item["postcode"] = match.group("postcode")
            item["city"] = match.group("city")

        return item
