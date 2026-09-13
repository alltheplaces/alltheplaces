from typing import Any, Iterable

from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS

# Both phone numbers found in the API response are shared national hotlines
# (33 and 25 of the 58 branches respectively), not branch-specific numbers.


class SummitCreditUnionUSSpider(CamoufoxSpider):
    name = "summit_credit_union_us"
    item_attributes = {"brand": "Summit Credit Union", "brand_wikidata": "Q7637799"}
    start_urls = ["https://www.summitcreditunion.com/api/locations/index.json"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json():
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]

            street_address_lines = [location["address"]["street"]]
            if (additional := location["address"].get("additionalStreet")) and additional.lower().startswith(
                ("suite", "ste", "room", "unit", "#")
            ):
                street_address_lines.append(additional)
            item["street_address"] = merge_address_lines(street_address_lines)

            item["city"] = location["address"]["city"]
            item["state"] = "WI"
            item["postcode"] = str(location["address"]["postalCode"])
            item["country"] = "US"

            item["branch"] = location["branchName"]
            item["name"] = self.item_attributes["brand"]
            item["website"] = "https://www.summitcreditunion.com" + location["slug"]

            item["opening_hours"] = self.parse_hours(location["features"])

            apply_category(Categories.BANK, item)
            services = location.get("services") or []
            apply_yes_no(Extras.ATM, item, "ATM" in services or "24-hour ATM" in services)
            apply_yes_no(Extras.DRIVE_THROUGH, item, any("Drive-thru" in s for s in services))

            yield item

    @staticmethod
    def parse_hours(features: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for feature in features:
            if feature.get("type") != "Lobby":
                continue
            for detail in feature.get("details", []):
                if "Holiday" in detail.get("title", ""):
                    continue
                if detail.get("status") != "Open":
                    continue
                if not detail.get("openTime") or not detail.get("closeTime"):
                    continue
                for day in DAYS_FULL:
                    if detail.get(day.lower()):
                        oh.add_range(day, detail["openTime"], detail["closeTime"])
        return oh
