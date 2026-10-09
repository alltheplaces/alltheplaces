import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class RoyalBankOfScotlandGBSpider(Spider):
    name = "royal_bank_of_scotland_gb"
    item_attributes = {"brand": "RBS", "brand_wikidata": "Q160126"}
    start_urls = ["https://openapi.rbs.co.uk/open-banking/v2.2/branches"]
    requires_proxy = False

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.text)
        for brand_data in data["data"]:
            for brand in brand_data["Brand"]:
                for branch in brand["Branch"]:
                    # Mobile branches have no reliable opening hours, so including them would suggest a branch where there is none
                    if branch.get("Type") == "Mobile":
                        continue
                    item = Feature()
                    postal_address = branch["PostalAddress"]

                    item["ref"] = branch["Identification"]
                    item["branch"] = branch["Name"].removeprefix("RBS ")

                    if address_lines := postal_address.get("AddressLine"):
                        item["street_address"] = address_lines[0]
                    item["city"] = postal_address.get("TownName")
                    item["postcode"] = postal_address.get("PostCode")
                    item["country"] = "GB"

                    if geo_location := postal_address.get("GeoLocation", {}).get("GeographicCoordinates"):
                        if lat := geo_location.get("Latitude"):
                            item["lat"] = float(lat)
                        if lon := geo_location.get("Longitude"):
                            item["lon"] = float(lon)

                    services = branch.get("ServiceAndFacility", [])
                    apply_yes_no(Extras.ATM, item, "ExternalATM" in services or "InternalATM" in services)
                    apply_yes_no(Extras.CASH_IN, item, "QuickDeposit" in services)

                    accessibility = branch.get("Accessibility", [])
                    apply_yes_no(Extras.WHEELCHAIR, item, "WheelchairAccess" in accessibility)

                    if availability := branch.get("Availability", {}).get("StandardAvailability", {}).get("Day"):
                        item["opening_hours"] = self.parse_opening_hours(availability)

                    apply_category(Categories.BANK, item)

                    yield item

    def parse_opening_hours(self, days: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for day in days:
            day_name = day.get("Name")
            if day_name in DAYS_FULL:
                for hours in day.get("OpeningHours", []):
                    opening_time = hours.get("OpeningTime")
                    closing_time = hours.get("ClosingTime")
                    if opening_time and closing_time:
                        oh.add_range(day_name, opening_time, closing_time)
        return oh
