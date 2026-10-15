from typing import AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.searchable_points import open_searchable_points


class DollaramaSpider(Spider):
    name = "dollarama"
    item_attributes = {"brand": "Dollarama", "brand_wikidata": "Q3033947"}
    allowed_domains = ["dollarama.com"]

    async def start(self) -> AsyncIterator[Request]:
        base_url = "https://www.dollarama.com/en-CA/locations/GetDataByCoordinates?"

        params = {"distance": "100", "units": "miles"}

        with open_searchable_points("ca_centroids_100mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                params |= {"latitude": lat, "longitude": lon}
                yield Request(url=base_url + urlencode(params), method="POST")

    def parse_hours(self, hours: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in DAYS:
            rule = hours[day]
            if rule["State"] == 1:
                opening_hours.set_closed(day)
                continue
            for time_range in rule["Ranges"]:
                opening_hours.add_range(day, time_range["StartTime"], time_range["EndTime"], "%I:%M%p")
        return opening_hours

    def parse(self, response):
        data = response.json()

        for row in data.get("StoreLocations", []):
            properties = {
                "ref": row["LocationNumber"],
                "name": row["Name"],
                "street_address": row["ExtraData"]["Address"]["AddressNonStruct_Line1"],
                "city": row["ExtraData"]["Address"]["Locality"],
                "state": row["ExtraData"]["Address"]["Region"],
                "postcode": row["ExtraData"]["Address"]["PostalCode"],
                "country": row["ExtraData"]["Address"]["CountryCode"],
                "lat": row["Location"]["coordinates"][1],
                "lon": row["Location"]["coordinates"][0],
            }

            if hours := row["ExtraData"].get("HoursOfOpStruct"):
                try:
                    properties["opening_hours"] = self.parse_hours(hours)
                except Exception as e:
                    self.logger.warning(f"Failed to parse opening hours for {hours}, {e}")
                    self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
            item = Feature(**properties)
            apply_category(Categories.SHOP_VARIETY_STORE, item)
            yield item
