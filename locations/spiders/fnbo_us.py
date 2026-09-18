from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# Maps each day name (used for the lobby hours fields, e.g. "Monday") to the
# corresponding drive-through hours field name (e.g. "DriveUpHrsMon").
DAY_TO_DRIVE_THROUGH_FIELD = {
    "Monday": "DriveUpHrsMon",
    "Tuesday": "DriveUpHrsTues",
    "Wednesday": "DriveUpHrsWed",
    "Thursday": "DriveUpHrsThurs",
    "Friday": "DriveUpHrsFri",
    "Saturday": "DriveUpHrsSat",
    "Sunday": "DriveUpHrsSun",
}


class FnboUSSpider(Spider):
    name = "fnbo_us"
    item_attributes = {"brand": "FNBO", "brand_wikidata": "Q5453412"}
    total_count = 0
    page_size = 0

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://clsws.locatorsearch.net/Rest/LocatorSearchAPI.svc/GetLocations",
            data={
                "NetworkId": 10100,
                "Latitude": 41.2604842,
                "Longitude": -95.9368662,
                "Miles": 3000,
                "SearchByOptions": "FCS, ATMSF, ATMDP",
                "PageIndex": page,
            },
            cb_kwargs={"current_page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        results = response.json()["data"]
        if not self.total_count:
            self.total_count = results["TotalRecCount"]
            self.page_size = results["PageSize"]

        for location in results.get("ATMInfo") or []:
            item = DictParser.parse(location)
            item.pop("street", None)
            item["street_address"] = location.get("Street")
            item["country"] = "US"
            item["branch"] = location["InstitutionName"]
            item["phone"] = location.get("WorkPhone") or None

            oh = OpeningHours()
            for day in DAY_TO_DRIVE_THROUGH_FIELD:
                if hours := location.get(day):
                    oh.add_ranges_from_string(f"{day} {hours}")
            if oh:
                item["opening_hours"] = oh

            if location["ServiceCenter"]:
                apply_category(Categories.BANK, item)

                drive_through_hours = OpeningHours()
                for day, drive_through_field in DAY_TO_DRIVE_THROUGH_FIELD.items():
                    if hours := location.get(drive_through_field):
                        drive_through_hours.add_ranges_from_string(f"{day} {hours}")
                if drive_through_hours:
                    item["extras"]["opening_hours:drive_through"] = drive_through_hours.as_opening_hours()
            else:
                apply_category(Categories.ATM, item)
                if (accept_deposit := location.get("AcceptDeposit")) is not None:
                    apply_yes_no(Extras.CASH_IN, item, accept_deposit, False)

            yield item

        if (kwargs["current_page"] * self.page_size) < self.total_count:
            yield self.make_request(kwargs["current_page"] + 1)
