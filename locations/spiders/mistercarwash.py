import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MisterCarWashSpider(scrapy.Spider):
    name = "mistercarwash"
    item_attributes = {"brand": "Mister Car Wash", "brand_wikidata": "Q114185788"}
    allowed_domains = ["mistercarwash.com/"]
    start_urls = [
        "https://mistercarwash.com/api/v1/locations/getbydistance?cLat=36.778261&cLng=-119.4179324&radius=10&cityName=California&stateName=&allServices=true"
    ]

    def parse(self, response):
        for location in response.json()["data"]["body"]["locationServicePriceDetailsModel"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["phone"] = location["contacts"][0]["phoneNumber"]

            hours_string = " ".join(
                f"{i['dayOfWeek']}: {i['localStartTime']}-{i['localEndTime']}" for i in location["hours"]
            )
            oh = OpeningHours()
            oh.add_ranges_from_string(hours_string)
            item["opening_hours"] = oh

            yield item
