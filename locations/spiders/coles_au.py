import math
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations, vincenty_distance
from locations.hours import OpeningHours, day_range


class ColesAUSpider(Spider):
    name = "coles_au"

    BRANDS = {
        2: {"brand": "Coles", "brand_wikidata": "Q1108172"},
        3: {"brand": "Liquorland", "brand_wikidata": "Q2283837"},
        4: {"brand": "First Choice Liquor", "brand_wikidata": "Q4596269"},
        5: {"brand": "Vintage Cellars", "brand_wikidata": "Q7932815"},
    }

    # The API returns at most 15 stores per search. In metro areas the 15th
    # nearest store can be only a few km away, so a single search cannot cover
    # a whole 20km grid cell. When a search is saturated, the cell is covered
    # again with 7 circles of half the radius (centre plus 6 around it at
    # sqrt(3)/2 of the radius), which fully cover the parent circle.
    MAX_STORES = 15
    START_RADIUS_KM = 20
    MIN_RADIUS_KM = 0.5

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in point_locations("au_centroids_20km_radius.csv"):
            yield self.make_request(lat, lon, self.START_RADIUS_KM)

    def make_request(self, lat: float, lon: float, radius_km: float) -> JsonRequest:
        return JsonRequest(
            f"https://apigw.coles.com.au/digital/colesweb/v1/stores/search?latitude={lat:.5f}&longitude={lon:.5f}&brandIds=1,2,3,4,5&numberOfStores={self.MAX_STORES}",
            meta={"lat": lat, "lon": lon, "radius_km": radius_km},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = response.json()["stores"]
        yield from self.parse_stores(stores)

        radius_km = response.meta["radius_km"]
        if len(stores) < self.MAX_STORES:
            return
        covered_km = max(store["distance"] for store in stores)
        # This search already stands in for the centre child, so only the 6
        # outer children are searched at each level. Descend through the
        # centre until this search covers it.
        lat, lon = response.meta["lat"], response.meta["lon"]
        while covered_km < radius_km and radius_km > self.MIN_RADIUS_KM:
            for bearing in range(0, 360, 60):
                child_lat, child_lon = vincenty_distance(lat, lon, radius_km * math.sqrt(3) / 2, bearing)
                yield self.make_request(child_lat, child_lon, radius_km / 2)
            radius_km /= 2

    def parse_stores(self, stores: list[dict]) -> Any:
        for location in stores:
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")

            if brand := self.BRANDS.get(location["brandId"]):
                item.update(brand)
            elif location["brandId"] == 1:
                continue
            else:
                self.logger.error("Unknown brand: {}".format(location["brandName"]))

            if location["brandId"] == 1:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            try:
                item["opening_hours"] = self.parse_opening_hours(location["tradingHours"])
            except:
                self.logger.error("Unable to parse opening hours: {}".format(location["tradingHours"]))

            yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if "-" in rule["daysOfWeek"]:
                days = day_range(*rule["daysOfWeek"].split("-"))
            else:
                days = [rule["daysOfWeek"]]

            if rule["storeTime"] == "24 hours":
                oh.add_days_range(days, "00:00", "24:00")
            elif rule["storeTime"] == "Closed":
                oh.set_closed(days)
            else:
                start_time, end_time = rule["storeTime"].split("-")
                if ":" not in start_time:
                    start_time = start_time.replace("am", ":00am").replace("pm", ":00pm")
                if ":" not in end_time:
                    end_time = end_time.replace("am", ":00am").replace("pm", ":00pm")
                oh.add_days_range(days, start_time, end_time, "%I:%M%p")

        return oh
