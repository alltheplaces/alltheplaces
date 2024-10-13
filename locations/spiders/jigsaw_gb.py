from typing import Any
import json

from scrapy.spiders import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours

class JigsawGBSpider(Spider):
    name = "jigsaw_gb"
    item_attributes = {"brand": "Jigsaw", "brand_wikidata": "Q6192383"}
    start_urls = ["https://jigsawimagestorage.blob.core.windows.net/jigsaw-logos/google-map-data-V3.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["features"]:
            newlocation = { key.replace('branch_', ''):value for key, value in location["properties"].items() }
            item = DictParser.parse(newlocation)
            item["branch"] = newlocation["name"]
            item["name"] = "Jigsaw"
            item["street_address"] = newlocation["address_2"]
            item["lat"],item["lon"]=location["geometry"]["coordinates"]

            opening_hours = OpeningHours()
            oh = newlocation["opening_hours"]
            oh=oh.replace("</li><li>",", ")
            oh=oh.replace("<li>","")
            oh=oh.replace("</li>","")
            days = oh.split(", ")
            for range in days:
                day,time_range=range.split(": ")
                time_range=time_range.replace(" ","")
                if "closed" not in time_range.lower():
                    open_time,close_time=time_range.split("-")
                    opening_hours.add_range(day, open_time, close_time)
                    item["opening_hours"]=opening_hours
            yield item
