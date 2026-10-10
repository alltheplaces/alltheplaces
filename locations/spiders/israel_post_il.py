from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature

BRANCH = 2  # סניף: post office run by Israel Post
AGENCY_TYPES = {
    3: "סוכנות א",  # agencies are franchised to third-party operators
    4: "סוכנות ב",
    5: "סוכנות ג",
}
FRONT_COUNTER = 10  # אשנב קדמי: small Israel Post counter inside an institution (e.g. a city hall)
VILLAGE_SECRETARIAT = 15  # מזכירות יישוב: postal counter run by a village/kibbutz/base secretariat
# Not emitted: 7 דואר נע (mobile post vans), 13 מסירת דואר בלבד (parcel pick-up points in shops),
# 14 אוטומטים (cash machines).


class IsraelPostILSpider(Spider):
    name = "israel_post_il"
    item_attributes = {"operator": "דואר ישראל", "operator_wikidata": "Q671700"}
    allowed_domains = ["mypostvouchars-prd.azureedge.net"]
    # Daily export behind the branch locator at https://doar.israelpost.co.il/locatebranch
    start_urls = ["https://mypostvouchars-prd.azureedge.net/branches/branches.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for unit in response.json()["Result"]:
            unit_type = unit["branchtype"]
            if unit["openstatus"] != 1:
                continue
            if unit_type not in (BRANCH, FRONT_COUNTER, VILLAGE_SECRETARIAT) and unit_type not in AGENCY_TYPES:
                continue

            item = Feature()
            item["ref"] = unit["branchnumber"]
            item["branch"] = unit["branchname"].strip()
            item["lat"], item["lon"] = unit["geocode_latitude"], unit["geocode_longitude"]
            item["street"] = unit["street"]
            if unit["street"] and unit["house"]:
                item["housenumber"] = str(unit["house"])
            elif not unit["street"] and unit["addressdesc"]:
                item["street_address"] = unit["addressdesc"]  # e.g. a mall or neighbourhood name
            item["city"] = unit["city"]
            item["postcode"] = unit["zip"]
            if unit["telephone"] and unit["telephone"] != "171":  # 171 is the national call centre
                item["phone"] = unit["telephone"]
            item["opening_hours"] = self.parse_hours(unit["hours"] or [])

            if unit_type in (BRANCH, FRONT_COUNTER):
                apply_category(Categories.POST_OFFICE, item)
            else:
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
            yield item

    @staticmethod
    def parse_hours(hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for day in hours:
            for n in ("1", "2"):
                start, end = day.get("openhour" + n), day.get("closehour" + n)
                if start and end:
                    # "dayofweek" runs from 1 (Sunday) to 7 (Saturday)
                    oh.add_range(DAYS_FROM_SUNDAY[day["dayofweek"] - 1], start, end, "%H:%M:%S")
        return oh
