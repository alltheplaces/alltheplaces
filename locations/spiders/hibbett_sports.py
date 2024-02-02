import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class HibbettSportsSpider(scrapy.Spider):
    name = "hibbett_sports"
    item_attributes = {"brand": "Hibbett Sports", "brand_wikidata": "Q5750671"}
    allowed_domains = ["hibbett.com"]
    start_urls = [
        "https://www.hibbett.com/on/demandware.store/Sites-Hibbett-US-Site/default/Stores-GetNearestStores?latitude=40.7127753&longitude=-74.0059728&countryCode=US&distanceUnit=mi&maxdistance=1000"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "US"

    def parse(self, response):
        for _, data in response.json().get("stores").items():
            item = DictParser.parse(data)
            item["street_address"] = item["street_address"].strip()
            oh = OpeningHours()
            for day in data.get("storeHoursFormatted"):
                if day[1] == "CLOSED":
                    continue
                opentime = day[1].split(" - ")[0]
                closetime = day[1].split(" - ")[1]
                oh.add_range(
                    day=day[0],
                    open_time=opentime if len(opentime) == (5 or 6) else f"{opentime[:1]}:00{opentime[-2:]}",
                    close_time=closetime if len(closetime) == (5 or 6) else f"{closetime[:1]}:00{closetime[-2:]}",
                    time_format="%I:%M%p",
                )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
