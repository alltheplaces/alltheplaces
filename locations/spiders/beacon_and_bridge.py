import scrapy
import re
from datetime import datetime
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from locations.hours import DAYS


class BeaconAndBridgeSpider(scrapy.Spider):
    name = "beacon_and_bridge"
    item_attributes = {"brand": "Beacon Bridge Market"}
    start_urls = ["https://beaconandbridge.com/locations/"]

    def parse(self, response):
        address_list = response.xpath(
            '//div[@id="section_2"]//div[contains(@class, "yes_heads")]'
        )
        for i, item in enumerate(address_list):
            hour = (
                item.xpath(f'//div[contains(@class, "yes_heads")][{i+1}]//p/text()[2]')
                .get()
                .replace("HOURS: ", "")
            )
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
                "ref": re.split(
                    " - | -",
                    item.xpath(
                        f'//div[contains(@class, "yes_heads")][{i+1}]//h3/text()'
                    ).get(),
                )[0],
                "name": re.split(
                    " - | -",
                    item.xpath(
                        f'//div[contains(@class, "yes_heads")][{i+1}]//h3/text()'
                    ).get(),
                )[1],
                "addr_full": item.xpath(
                    f'//div[contains(@class, "yes_heads")][{i+1}]//span/a/text()[1]'
                ).get(),
                "city": item.xpath(
                    f'//div[contains(@class, "yes_heads")][{i+1}]//span/a/text()[2]'
                )
                .get()
                .split(", ")[0],
                "state": item.xpath(
                    f'//div[contains(@class, "yes_heads")][{i+1}]//span/a/text()[2]'
                )
                .get()
                .split(", ")[1],
                "postcode": item.xpath(
                    f'//div[contains(@class, "yes_heads")][{i+1}]//span/a/text()[3]'
                ).get(),
                "phone": item.xpath(
                    f'//div[contains(@class, "yes_heads")][{i+1}]//p/text()[1]'
                )
                .get()
                .replace("PHONE: ", ""),
                "opening_hours": oh.as_opening_hours(),
            }

            yield GeojsonPointItem(**properties)
