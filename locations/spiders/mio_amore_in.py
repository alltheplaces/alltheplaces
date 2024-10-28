import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MioAmoreINSpider(Spider):
    name = "mio_amore_in"
    item_attributes = {"brand": "Mio Amore", "brand_wikidata": "Q130534919"}
    start_urls = ["https://storelocator.mioamoreshop.com/wp-content/uploads/agile-store-locator/locator-data.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street"] = None
            item["street_address"] = location["description"]
            item["extras"]["fax"] = location["fax"]

            item["opening_hours"] = OpeningHours()
            for day, times in json.loads(location["open_hours"]).items():
                for time in times:
                    if time == "0":
                        item["opening_hours"].set_closed(day)
                    else:
                        item["opening_hours"].add_range(day, *time.split(" - "), time_format="%I:%M %p")

            yield item
