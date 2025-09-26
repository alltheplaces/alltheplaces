import json
from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class FlightCentreAUSpider(Spider):
    name = "flight_centre_au"
    item_attributes = {"brand": "Flight Centre", "brand_wikidata": "Q5459202"}
    start_urls = ["https://www.flightcentre.com.au/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath('//*[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"][
            "countryStores"
        ]:
            if location.get("geo_location"):
                location.update(location.pop("geo_location"))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Flight Centre ")
            item["website"] = urljoin("https://www.flightcentre.com.au/stores/", location["slug"])
            oh = OpeningHours()
            for day_time in location["opening_hours"]:
                if day_time["closed"]:
                    oh.set_closed(day_time["day"])
                else:
                    oh.add_range(day_time.get("day"), day_time.get("open"), day_time.get("close"))
            item["opening_hours"] = oh
            yield item
