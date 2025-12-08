import json

import scrapy

from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature


class EpNLSpider(scrapy.Spider):
    name = "ep_nl"
    start_urls = ["https://www.ep.nl/winkels/"]

    item_attributes = {"brand": "EP:", "brand_wikidata": "Q110271192"}

    def parse(self, response, **kwargs):
        raw = response.xpath("//div[@id='content']/script/text()").extract_first()
        raw = raw.replace("pageData.push({ stores: ", "").replace("});", "")
        stores_json = json.loads(raw)
        for store in stores_json.get("stores"):
            oh = OpeningHours()
            for day in store.get("openingHours"):
                hours = day.get("openingHours").replace(" - ", "-")
                if hours == "":
                    continue
                for hour in hours.split(" "):
                    open_time, close_time = hour.split("-")
                    oh.add_range(
                        day=DAYS_NL[day.get("weekDay")], open_time=open_time, close_time=close_time, time_format="%H:%M"
                    )
            yield Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("name"),
                    "street_address": store.get("street"),
                    "addr_full": ", ".join(
                        filter(None, [store.get("street"), store.get("zipcode"), store.get("city")])
                    ),
                    "phone": store.get("phoneNumber"),
                    "email": store.get("email"),
                    "postcode": store.get("zipcode"),
                    "city": store.get("city"),
                    "website": store.get("link"),
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                }
            )
