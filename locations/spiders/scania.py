import re
from copy import deepcopy
from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature

SCANIA_SHARED_ATTRIBUTES = {"brand": "Scania", "brand_wikidata": "Q219960"}


class ScaniaSpider(scrapy.Spider):
    name = "scania"
    start_urls = ["https://www.scania.com/group/en/home/admin/misc/sales-region.html"]

    TRUCK_SALE_CODES = ["trucksales", "usedvehiclessales"]
    TRUCK_SERVICE_CODES = ["truckservice"]
    TRUCK_PARTS_CODES = ["scaniapartssales"]
    MARINE_SERVICE_CODES = ["marineenginesservice"]
    POWER_ENGINE_CODES = ["industrialpowergenerationenginessales", "industrialpowergenerationenginesservice"]

    SERVICE_EXTRAS_MAPPING = {
        "vehiclewashing": Extras.TRUCK_WASH,
        "tyreservice": Extras.VEHICLE_TYRE_REPAIR_SERVICES,
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        websites = response.xpath('//*[@class="cmp-teaser__action-link"]/@href').getall()
        for country_website in websites:
            if m := re.search(r"https://www.scania.com/(.*)/(.*)/", country_website):
                country, language = m.groups()
            yield JsonRequest(
                url="https://www.scania.com/api/sis.json?type=DealerV2&country={}&currentPage=/content/www/{}/{}/home/admin/misc/dealer/contact-locator".format(
                    country.upper(), country, language
                ),
                callback=self.parse_stores,
            )

    def parse_stores(self, response: Response):
        if not response.body:
            return  # 0 locations, eg cuba
        for store in response.json().get("dealers"):
            item = Feature()
            item["ref"] = store.get("scaniaId")
            item["country"] = store.get("domicileCountry").get("countryCode")
            legal_address = store.get("legalAddress").get("postalAddress").get("physicalAddress")

            address_details = store.get("visitingAddress")
            item["name"] = address_details.get("addressee")
            item["phone"] = address_details.get("fixedPhoneNumber").get("subscriberNumber")
            item["email"] = address_details.get("electronicMailAddress")

            postal_address = address_details.get("postalAddress").get("physicalAddress")
            item["street_address"] = postal_address.get("street").get("streetName").get("value")
            item["city"] = postal_address.get("city").get("value")
            item["state"] = postal_address.get("countryRegion", {}).get("value")
            item["postcode"] = postal_address.get("postalCode")

            postal_coordinates = postal_address.get("coordinates", {})
            legal_coordinates = legal_address.get("coordinates", {})

            item["lat"] = postal_coordinates.get("latitude") or legal_coordinates.get("latitude")
            item["lon"] = postal_coordinates.get("longitude") or legal_coordinates.get("longitude")

            item["opening_hours"] = self.parse_hours(store.get("openingHours", []))

            provided_services = store.get("providedServices", [])
            service_codes = [ps.get("DealerServiceCode", ps.get("dealerServiceCode")) for ps in provided_services]

            # MAJORITY_OWNER - official dealership
            # MINORITY_OWNER - 3rd party
            scania_ownership = store.get("scaniaOwnership")

            if scania_ownership == "MAJORITY_OWNER":
                item.update(SCANIA_SHARED_ATTRIBUTES)

            is_truck_sale = any(code in self.TRUCK_SALE_CODES for code in service_codes)
            is_truck_service = any(code in self.TRUCK_SERVICE_CODES for code in service_codes)
            is_engine_service = any(code in self.POWER_ENGINE_CODES for code in service_codes)
            is_truck_service = is_truck_service or (is_engine_service and scania_ownership == "MAJORITY_OWNER")
            is_marine_service = any(code in self.MARINE_SERVICE_CODES for code in service_codes)
            is_truck_parts = any(code in self.TRUCK_PARTS_CODES for code in service_codes)

            if is_truck_sale:
                yield self.build_item_with_category(Categories.SHOP_TRUCK, item, service_codes)

            if is_truck_service:
                yield self.build_item_with_category(Categories.SHOP_TRUCK_REPAIR, item, service_codes)

            if not is_truck_sale and not is_truck_service:
                if is_marine_service:
                    yield self.build_item_with_category(Categories.SHOP_BOAT_REPAIR, item, [])
                elif is_engine_service:
                    # POIs with MINORITY_OWNER and engine services refer to construction equipment supplier / construction machine dealer
                    yield self.build_item_with_category(Categories.SHOP_PLANT_HIRE, item, [])
                elif is_truck_parts:
                    yield self.build_item_with_category(Categories.SHOP_TRUCK_PARTS, item, [])

    def build_item_with_category(self, category: Categories, item: Feature, extras: list[str]):
        categorized_item = deepcopy(item)
        categorized_item["ref"] = f"{item['ref']}-{category}"
        apply_category(category, categorized_item)
        for extra in extras:
            if match := self.SERVICE_EXTRAS_MAPPING.get(extra):
                apply_yes_no(match, categorized_item, True)
        return categorized_item

    def parse_hours(self, opening_hours: list[dict]) -> OpeningHours | None:
        oh = OpeningHours()
        for ohs in opening_hours:
            for day in ohs.get("days", []):
                for hours in ohs.get("openTimes", []):
                    try:
                        oh.add_range(
                            day=sanitise_day(day), open_time=hours.get("timeFrom"), close_time=hours.get("timeTo")
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to parse hours: {e}")
                        return None
        return oh
