from datetime import datetime
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksARCLSpider(JSONBlobSpider):
    name = "starbucks_ar_cl"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES

    async def start(self) -> AsyncIterator[JsonRequest]:
        for country, base_url, min_population in [
            ("AR", "https://www.starbucks.com.ar", 100000),
            ("CL", "https://www.starbucks.cl", 15000),
        ]:
            for city in city_locations(country, min_population):
                yield JsonRequest(
                    url=f"{base_url}/api/getStores",
                    data=[city["latitude"], city["longitude"], "100000"],
                )

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("store", {}))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["street_address"] = merge_address_lines(
            [feature["address"].get("streetAddressLine1"), feature["address"].get("streetAddressLine2")]
        )
        item["state"] = feature["address"].get("countrySubdivisionCode")
        if item["phone"] == "null":
            item["phone"] = None

        schedule = feature.get("hoursNext7Days", {}).get("dailySchedule") or []
        try:
            item["opening_hours"] = self.parse_opening_hours(schedule)
        except Exception as e:
            self.logger.warning(f"Failed to parse opening hours: {schedule} {e}")

        item["website"] = response.url.replace("/api/getStores", "/stores")

        if services := feature.get("features", {}).get("feature", []):
            service_codes = [service.get("code") for service in services]
            apply_yes_no(Extras.WIFI, item, "WF" in service_codes)
            apply_yes_no(Extras.DELIVERY, item, "DE" in service_codes)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "DT" in service_codes)
            apply_yes_no(Extras.TOILETS, item, "WC" in service_codes)
        apply_category(Categories.COFFEE_SHOP, item)
        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            day = datetime.strptime(rule.get("date").split(".")[0], "%Y-%m-%dT%H:%M:%S").strftime("%A")
            if rule.get("openTime") and rule.get("closeTime"):
                if "Cerrado" in rule["openTime"].title():
                    opening_hours.set_closed(day)
                    continue
                time_format = "%I:%M:%S %p" if "M" in rule["openTime"] else "%H:%M:%S"
                opening_hours.add_range(day, rule["openTime"], rule["closeTime"], time_format)
        return opening_hours
