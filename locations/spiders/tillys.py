import re

import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature

AM_PM = r"am|pm|a.m.|p.m.|a|p"


class TillysSpider(scrapy.Spider):
    name = "tillys"
    item_attributes = {"brand": "Tillys", "brand_wikidata": "Q7802889"}
    start_urls = [
        "https://www.tillys.com/on/demandware.store/Sites-tillys-Site/default/Stores-FindStores?showMap=false&isAjax=false&location=66952&radius=10000"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        results = response.json()
        for data in results["stores"]:
            oh = OpeningHours()
            html_oh = data.get("storeHours")
            if html_oh:
                oh_str = html_oh.lstrip(
                    '<div style="width:30%; position:relative; float:left;">Monday<br />\nTuesday<br />\nWednesday<br />\nThursday<br />\nFriday<br />\nSaturday<br />\nSunday</div>\n\n<div style="width:70%; position:relative; float:right;">'
                ).rstrip("</div>")
                oh_elements = oh_str.split("<br />\n")
                oh_elements = [x.replace("<br ", "") for x in oh_elements]
            for i, day in enumerate(DAYS):
                current_oh = oh_elements[i].split(" - ")
                current_oh = [re.sub(AM_PM, "", o) for o in current_oh]
                oh.add_range(
                    day=day,
                    open_time=current_oh[0],
                    close_time=current_oh[1],
                    time_format="%H:%M",
                )

            props = {
                "ref": data.get("ID"),
                "name": data.get("name"),
                "street_address": data.get("address1"),
                "city": data.get("city"),
                "postcode": data.get("postalCode"),
                "state": data.get("stateCode"),
                "phone": data.get("phone"),
                "country": data.get("countryCode"),
                "opening_hours": oh.as_opening_hours(),
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
            }

            yield Feature(**props)
