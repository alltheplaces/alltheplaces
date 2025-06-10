import json

import scrapy

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import DAYS, OpeningHours


class KayJewelersSpider(scrapy.Spider):
    name = "kay_jewelers"
    item_attributes = {"brand": "Kay Jewelers", "brand_wikidata": "Q62029290"}

    def start_requests(self):
        for lat, lon in point_locations("us_centroids_50mile_radius.csv"):
            url = (
                f"https://stores.kay.com/umbraco/api/search/GetDataByCoordinates?longitude={lon}&latitude={lat}"
                f"&distance=50&units=miles" + "&filter={%22ReportGroup%22:%22Kay%22}"
            )
            yield scrapy.http.JsonRequest(url)

    def parse(self, response):
        data = json.loads(response.json())["StoreLocations"]
        if len(data) > 0:
            for poi in data:
                poi_addr = poi["ExtraData"]["Address"]
                item = DictParser.parse(poi)
                item["street_address"] = poi.get("Address")
                item["state"] = poi_addr.get("Region")
                item["country"] = poi_addr.get("CountryCode")
                item["city"] = poi_addr.get("Locality")
                item["postcode"] = poi_addr.get("PostalCode")
                item["phone"] = poi["ExtraData"]["Phone"]
                item["ref"] = poi["ExtraData"]["ReferenceCode"]
                coords = poi["Location"]["coordinates"]
                item["lon"], item["lat"] = coords[0], coords[1]

                self.opening_hours(poi["ExtraData"].get("HoursOfOpStruct"), item)
                item["street_address"] = item.pop("addr_full", None)
                yield item

    def opening_hours(self, hours, item):
        if not hours:
            return

        oh = OpeningHours()
        for day, info in hours.items():
            if day in DAYS:
                if times := info["Ranges"]:
                    for time in times:
                        oh.add_range(day, time["StartTime"], time["EndTime"], "%I:%M%p")
        item["opening_hours"] = oh
