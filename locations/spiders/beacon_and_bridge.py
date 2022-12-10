import scrapy
import re
from datetime import datetime
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class BeaconAndBridgeSpider(scrapy.Spider):
    name = "beacon_and_bridge"
    item_attributes = {"brand": "Beacon Bridge Market"}
    start_urls = ["https://beaconandbridge.com/locations/"]

    def parse(self, response):
        address_full = response.xpath('//div[@id="section_2"]//span/a/text()[1]')
        city_state = response.xpath('//div[@id="section_2"]//span/a/text()[2]')
        postcode = response.xpath('//div[@id="section_2"]//span/a/text()[3]')
        names = response.xpath('//div[@id="section_2"]//h3/text()')
        phones = response.xpath('//div[@id="section_2"]//p/text()[1]')
        hours = response.xpath('//div[@id="section_2"]//p/text()[2]')
        for (
            addr,
            cs,
            postcd,
            name,
            phone,
            hour,
        ) in zip(address_full, city_state, postcode, names, phones, hours):
            hour = hour.get().replace("HOURS: ", "")
            oh = OpeningHours()
            for day in DAYS:
                if hour == "24/7":
                    hour = "12:00am - 12:00am"
                h_h = re.split(" - | -", hour)
                oh.add_range(
                    day=day,
                    open_time=datetime.strftime(
                        datetime.strptime(
                            h_h[0].replace("am", " am").replace("pm", " pm"),
                            "%I:%M %p",
                        ),
                        "%H:%M",
                    ),
                    close_time=datetime.strftime(
                        datetime.strptime(
                            h_h[1].replace("am", " am").replace("pm", " pm"),
                            "%I:%M %p",
                        ),
                        "%H:%M",
                    ),
                )
            properties = {
                "ref": re.split(" - | -", name.get())[0],
                "name": re.split(" - | -", name.get())[1],
                "addr_full": addr.get(),
                "city": cs.get().split(", ")[0],
                "state": cs.get().split(", ")[1],
                "postcode": postcd.get(),
                "phone": phone.get().replace("PHONE: ", ""),
                "opening_hours": oh.as_opening_hours(),
            }

            yield GeojsonPointItem(**properties)
