import re

from scrapy import Spider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class BeaconAndBridgeMarketUSSpider(Spider):
    name = "beacon_and_bridge_market_us"
    item_attributes = {"brand": "Beacon & Bridge Market", "brand_wikidata": "Q122209684"}
    start_urls = ["https://beaconandbridge.com/locations/"]

    def parse(self, response):
        address_list = response.xpath('//div[@id="section_2"]//div[contains(@class, "yes_heads")]')
        for store in address_list:
            hour = store.xpath(".//p/text()[2]").get().replace("HOURS: ", "")
            oh = OpeningHours()
            for day in DAYS:
                if hour == "24/7":
                    hour = "12:00am - 12:00am"
                h_h = re.split(" - | -", hour)
                oh.add_range(
                    day=day,
                    open_time=h_h[0],
                    close_time=h_h[1],
                    time_format="%I:%M%p",
                )
            properties = {
                "ref": store.xpath(".//h3/text()").get(),
                "name": store.xpath(".//h3/text()").get(),
                "street_address": store.xpath(".//span/a/text()[1]").get(),
                "city": store.xpath(".//span/a/text()[2]").get().split(", ")[0],
                "state": store.xpath(".//span/a/text()[2]").get().split(", ")[1],
                "postcode": store.xpath(".//span/a/text()[3]").get(),
                "phone": store.xpath(".//p/text()[1]").get().replace("PHONE: ", ""),
                "opening_hours": oh.as_opening_hours(),
            }

            yield Feature(**properties)
