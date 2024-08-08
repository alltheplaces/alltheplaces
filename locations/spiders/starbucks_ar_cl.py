from datetime import datetime

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class StarbucksARCLSpider(Spider):
    name = "starbucks_ar_cl"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158"}

    def start_requests(self):
        for country, base_url, min_population in [
            ("AR", "https://www.starbucks.com.ar", 100000),
            ("CL", "https://www.starbucks.cl", 15000),
        ]:
            for city in city_locations(country, min_population):
                yield JsonRequest(
                    url=f"{base_url}/api/getStores",
                    data=[city["latitude"], city["longitude"], "100000"],
                )

    def parse(self, response, **kwargs):
        for location in response.json():
            store = location.get("store")
            item = DictParser.parse(store)
            item["street_address"] = merge_address_lines(
                [store["address"].get("streetAddressLine1"), store["address"].get("streetAddressLine2")]
            )
            item["state"] = store["address"].get("countrySubdivisionCode")
            if item["phone"] == "null":
                item["phone"] = None
            oh = OpeningHours()
            for rule in store.get("hoursNext7Days", {}).get("dailySchedule", []):
                day = datetime.strptime(rule.get("date").split(".")[0], "%Y-%m-%dT%H:%M:%S").weekday()
                if rule.get("openTime") and rule.get("closeTime"):
                    oh.add_range(DAYS[day], rule["openTime"], rule["closeTime"], "%H:%M:%S")
            item["opening_hours"] = oh.as_opening_hours()
            item["website"] = response.url.replace("/api/getStores", "/stores")

            if services := store.get("features", {}).get("feature"):
                service_codes = [service.get("code") for service in services]
                apply_yes_no(Extras.WIFI, item, "WF" in service_codes)
                apply_yes_no(Extras.DELIVERY, item, "DE" in service_codes)
                apply_yes_no(Extras.DRIVE_THROUGH, item, "DT" in service_codes)
                apply_yes_no(Extras.TOILETS, item, "WC" in service_codes)
            apply_category(Categories.COFFEE_SHOP, item)
            yield item
