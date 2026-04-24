from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class SylinderSpider(Spider):
    """
    To use this store finder, specify one or more brand/application keys using
    the 'app_keys' attribute of this class. Also specify a 'base_url' value
    which is prefixed to store identifiers to generate a website field value
    for each extracted feature.

    If required, override the 'parse_item' method to extract additional
    location data or to clean up and modify extracted data.
    """

    dataset_attributes: dict = {"source": "api", "api": "api.ngadata.no"}

    app_keys: list[str]
    base_url: str | None = None
    warn_if_no_base_url: bool = True
    shop_service_post_partners = {
        "DHL": "DHL",
        "HELTHJEM": "Helthjem",
        "MYP": "PostNord",
        "PIB": "Posten",
    }
    shop_service_parcel_pickup = {
        "INSTABOX_I": "Instabox",
        "INSTABOX_U": "Instabox",
        "PN_PB_U": "PostNord",
        "PP": "Posten",
        "P_PB_U": "Posten",
    }

    def chain_ids(self) -> set[str]:
        return set(self.app_keys)

    def apply_shop_services(self, item: Feature, location: dict) -> None:
        for service in location.get("shopServices", []):
            match service["typeCode"]:
                case "BAX_NT" | "BAX_RT":  # BAX_NT = Tipping / BAX_RT = Rikstoto
                    apply_yes_no("lottery", item, True)
                case "CAT":
                    apply_yes_no("catering", item, True)
                case "KIB":
                    apply_yes_no(Extras.CASH_IN, item, True)
                    apply_yes_no("cash_withdrawal", item, True)
                case "ZPROPN":
                    apply_yes_no(Fuel.PROPANE, item, True)
                case code if brand := self.shop_service_post_partners.get(code):
                    apply_category({"post_office": "post_partner", "post_office:brand": brand}, item)
                case code if brand := self.shop_service_parcel_pickup.get(code):
                    apply_category({"post_office:parcel_pickup": brand}, item)

    async def start(self) -> AsyncIterator[JsonRequest]:
        if self.base_url is None and self.warn_if_no_base_url:
            self.logger.warning("Specify self.base_url to allow extraction of website values for each feature.")
        chain_ids = self.chain_ids()
        url = "https://api.ngdata.no/sylinder/stores/v1/extended-info"
        if len(chain_ids) == 1:
            url += f"?chainId={next(iter(chain_ids))}"
        yield JsonRequest(url=url)

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        chain_ids = self.chain_ids()
        for location in response.json():
            if location["storeDetails"]["chainId"] in chain_ids:
                yield from self.parse_location(location) or []

    def parse_location(self, location: dict) -> Iterable[Feature]:
        location = {**location, **location.pop("storeDetails")}
        location = {**location, **location.pop("organization")}

        item = DictParser.parse(location)
        item["ref"] = location["gln"]

        if self.base_url is not None:
            item["website"] = f"{self.base_url}{location['slug']}"

        self.apply_shop_services(item, location)

        if opening_hours := location.get("openingHours"):
            item["opening_hours"] = OpeningHours()
            # For now, not collecting special opening hours
            # print(location["openingHours"]["upcomingSpecialOpeningHours"])
            for day in opening_hours["upcomingOpeningHours"]:
                if day["isSpecial"] is True:
                    continue
                elif day["closed"] is True:
                    item["opening_hours"].set_closed(day["abbreviatedDayOfWeek"])
                else:
                    item["opening_hours"].add_range(day["abbreviatedDayOfWeek"], day["opens"], day["closes"])

        yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        yield item
