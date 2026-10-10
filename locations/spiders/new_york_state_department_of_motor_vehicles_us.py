from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.socrata import SocrataSpider


class NewYorkStateDepartmentOfMotorVehiclesUSSpider(SocrataSpider):
    name = "new_york_state_department_of_motor_vehicles_us"
    item_attributes = {
        "name": "Department of Motor Vehicles",
        "operator": "New York State Department of Motor Vehicles",
        "operator_wikidata": "Q17109616",
        "state": "NY",
        "country": "US",
    }
    host = "data.ny.gov"
    resource_id = "9upz-c7xg"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("office_name")
        item["branch"] = feature.get("office_name")

        street_address = feature.get("street_address_line_1") or ""
        if line_2 := feature.get("street_address_line_2"):
            street_address = f"{street_address}, {line_2}"
        item["street_address"] = street_address

        item["phone"] = feature.get("public_phone_number")

        oh = OpeningHours()
        for day, field_prefix in zip(DAYS, ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]):
            open_time = feature.get(f"{field_prefix}_beginning_hours")
            close_time = feature.get(f"{field_prefix}_ending_hours")
            oh.add_range(day, open_time, close_time, time_format="%I:%M %p")
        # The dataset has no Sunday columns at all; DMV offices are never open Sundays.
        oh.add_range("Su", "CLOSED", "CLOSED")
        item["opening_hours"] = oh

        apply_category({"office": "government"}, item)
        item.set_tag("government", "vehicle_registration")

        yield item
