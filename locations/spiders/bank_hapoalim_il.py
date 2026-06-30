from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class BankHapoalimILSpider(Spider):
    name = "bank_hapoalim_il"
    item_attributes = {"brand": "בנק הפועלים", "brand_wikidata": "Q2666775"}
    requires_proxy = True  # Incapsula blocks direct requests.

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url="https://www.bankhapoalim.co.il/he/api/branches/data")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = self.parse_location(location)
            if not item:
                continue

            if opening_hours := self.parse_opening_hours(location):
                item["opening_hours"] = opening_hours

            if location.get("channelsGroupCode") == 19:
                if branch := item.pop("name", None):
                    item["branch"] = branch
                apply_yes_no(Extras.ATM, item, self.has_service(location, 11))
                apply_yes_no(Extras.WHEELCHAIR, item, self.has_accessibility(location, 2))
                apply_category(Categories.BANK, item)
            elif location.get("channelsGroupCode") == 899:
                apply_yes_no(Extras.CASH_IN, item, self.has_service(location, 11))
                apply_yes_no(Extras.CASH_OUT, item, self.has_service(location, 11))
                apply_category(Categories.ATM, item)
            else:
                self.logger.error("Unexpected channelsGroupCode: {}".format(location.get("channelsGroupCode")))
                continue

            yield item

    def parse_location(self, location: dict[str, Any]) -> Feature | None:
        address = (location.get("geographicAddress") or [{}])[0] or {}
        coordinates = address.get("geographicCoordinate") or {}
        if not (coordinates.get("geoCoordinateX") and coordinates.get("geoCoordinateY")):
            return None

        item = DictParser.parse(location)
        item["ref"] = str(location.get("branchNumber"))
        item["lon"] = coordinates.get("geoCoordinateX")
        item["lat"] = coordinates.get("geoCoordinateY")
        item["street_address"] = self.build_street_address(address)
        item["city"] = address.get("cityName")

        if postcode := address.get("zipCode"):
            item["postcode"] = str(postcode)

        item.pop("phone", None)
        item.pop("email", None)
        item.pop("website", None)

        return item

    def parse_opening_hours(self, location: dict[str, Any]) -> OpeningHours | None:
        opening_hours = OpeningHours()

        try:
            for day_name, day in (
                ((location.get("availability") or {}).get("availabilityStandard") or {})
                .get("weekDaysSpecification", {})
                .items()
            ):
                osm_day = DAYS_EN.get(day_name.title())
                if not osm_day:
                    continue

                for rule in (day or {}).get("branchOpeningHours") or []:
                    if rule.get("startHour") and rule.get("endHour"):
                        opening_hours.add_range(osm_day, rule["startHour"], rule["endHour"])
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            self.logger.warning("Could not parse opening hours for {}: {}".format(location.get("branchNumber"), e))
            return None

        return opening_hours or None

    @staticmethod
    def build_street_address(address: dict[str, Any]) -> str | None:
        return " ".join(filter(None, [address.get("streetName"), address.get("buildingNumber")])) or None

    @staticmethod
    def has_service(location: dict[str, Any], service_code: int) -> bool:
        return any(
            service.get("branchServiceTypeCode") == service_code and service.get("serviceSwitch") == "yes"
            for service in location.get("branchService") or []
        )

    @staticmethod
    def has_accessibility(location: dict[str, Any], accessibility_code: int) -> bool:
        return any(
            accessibility.get("accessibilityTypeCode") == accessibility_code
            and accessibility.get("accessibilityTypeSwitch") == "1"
            for accessibility in location.get("accessibility") or []
        )
