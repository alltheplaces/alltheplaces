from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AceParkingUSSpider(JSONBlobSpider):
    name = "ace_parking_us"
    item_attributes = {"brand": "Ace Parking", "brand_wikidata": "Q108274179"}
    locations_key = "results"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids("US", 158):
            yield JsonRequest(
                url=f"https://aceparking.com/wp-json/ace-parking/v1/find-parking?lat={lat}&lng={lon}",
            )

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full", None)
        item["website"] = None
        try:
            item["opening_hours"] = self.parse_opening_hours(feature.get("hours", {}))
        except Exception as e:
            self.logger.error(f'Error parsing opening hours for {feature.get("hours")}: {e}')
        apply_category(Categories.PARKING, item)
        apply_yes_no(Fuel.ELECTRIC, item, feature.get("evChargers"))
        yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours | None:
        if not rules:
            return None
        opening_hours = OpeningHours()
        for rule in rules:
            if day := sanitise_day(rule):
                hours = rules[rule]
                if not hours:
                    continue
                elif "Closed" in hours:
                    opening_hours.set_closed(day)
                    continue
                elif "2400" in hours:
                    open_time, close_time = "00:00", "23:59"
                else:
                    open_time, close_time = [f"{t[:-2]}:{t[-2:]}" for t in hours]
                opening_hours.add_range(day, open_time, close_time)
        return opening_hours
