import json

import scrapy

from locations.categories import Categories
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class DockxBESpider(scrapy.Spider):
    name = "dockx_be"
    start_urls = ["https://www.dockx.be/en/locations"]

    item_attributes = {"brand": "Dockx", "extras": Categories.CAR_RENTAL.value}

    def parse(self, response, **kwargs):
        raw = (
            response.xpath('//*[@id="main"]/section/div/div/div/script[3]/text()')
            .extract_first()
            .replace(
                'window.addEventListener("load",function(){if(typeof window.initializeComponent!=="undefined")initializeComponent("DealerLocatorWidget",',
                "",
            )
        )[:-43]
        stores_json = json.loads(raw)
        for store in stores_json.get("dealers"):
            coordinates = store.get("coordinates")
            address_details = store.get("address")
            oh = OpeningHours()
            for hours in store.get("openingHours").values():
                day = DAYS_EN.get(hours.get("weekday").capitalize())
                oh.add_range(
                    day=day,
                    open_time=hours.get("startAm"),
                    close_time=hours.get("endAm"),
                )
                if hours.get("startPm") and hours.get("endPm"):
                    oh.add_range(
                        day=day,
                        open_time=hours.get("startPm"),
                        close_time=hours.get("endPm"),
                    )
            yield Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("name"),
                    "street": address_details.get("street"),
                    "housenumber": address_details.get("number"),
                    "postcode": address_details.get("postalCode"),
                    "city": address_details.get("city"),
                    "country": address_details.get("country"),
                    "addr_full": store.get("labelAddress"),
                    "phone": store.get("phoneNumber"),
                    "email": store.get("emailAddress"),
                    "website": f"https://www.dockx.be/en/locations/{store.get('slug')}",
                    "lat": coordinates.get("latitude"),
                    "lon": coordinates.get("longitude"),
                    "opening_hours": oh,
                }
            )
