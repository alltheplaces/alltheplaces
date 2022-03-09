import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "Montag": "Mo",
    "Dienstag": "Tu",
    "Mittwoch": "We",
    "MIttwoch": "We",
    "Donnerstag": "Th",
    "Donnertag": "Th",
    "Freitag": "Fr",
    "Samstag": "Sa",
    "Sonntag": "Su",
}


class DennsDeSpider(scrapy.Spider):
    name = "denns_de"
    allowed_domains = ["www.biomarkt.de"]
    start_urls = [
        "https://www.biomarkt.de/api/es/market/_search/?source=%7B%22from%22:0,%22size%22:1000,%22sort%22:[],%22query%22:%7B%22bool%22:%7B%22must%22:[]%7D%7D%7D&source_content_type=application%2Fjson"
    ]
    download_delay = 0.2

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in store_hours:
            opening_hours.add_range(
                day=DAY_MAPPING[store_day["weekday"].strip()],
                open_time=store_day["open_from"],
                close_time=store_day["open_until"],
                time_format="%H:%M",
            )
        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = json.loads(response.text)
        stores = data["hits"]["hits"]
        for store in stores:
            properties = {
                "ref": store["_id"],
                "street": store["_source"]["address.street"],
                "city": store["_source"]["address.city"],
                "postcode": store["_source"]["address.zip"],
                "country": store["_source"].get("countryCode", ""),
                "lat": store["_source"].get("address.lat", ""),
                "lon": store["_source"].get("address.lon", ""),
                "phone": store["_source"].get("contact.phone", ""),
            }

            hours = self.parse_hours(store["_source"]["openingHoursMarket"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
