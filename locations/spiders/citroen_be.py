import scrapy

from locations.hours import DAYS_FR, DAYS_NL, OpeningHours, sanitise_day
from locations.items import Feature


class CitroenBESpider(scrapy.Spider):
    name = "citroen_be"
    item_attributes = {"brand": "Citroen", "brand_wikidata": "Q6746"}
    start_urls = [
        "https://www.citroen.be/apps/atomic/DealersServlet?distance=30000&latitude=50.84439&longitude=4.35608&maxResults=1000&orderResults=false&path=L2NvbnRlbnQvY2l0cm9lbi93b3JsZHdpZGUvYmVsZ2l1bS9mcl9mcg%3D%3D&searchType=latlong"
    ]

    def parse(self, response, **kwargs):
        for store in response.json().get("payload").get("dealers"):
            address_details = store.get("address")
            contact_details = store.get("generalContact")
            coordinates = store.get("geolocation")
            oh = OpeningHours()
            if ohs := store.get("generalOpeningHour"):
                ohs = ohs.split("<br />")
                for day in ohs:
                    if ":" not in day or "gesloten" in day.lower():
                        continue
                    day, hours = day.split(":", maxsplit=1)
                    day = sanitise_day(day, {**DAYS_NL, **DAYS_FR})
                    for hours in hours.split(" "):
                        if "-" in hours:
                            start, end = hours.split("-", maxsplit=1)
                            oh.add_range(day, start, end, time_format="%H:%M")

            yield Feature(
                {
                    "ref": store.get("rrdi"),
                    "name": store.get("dealerName"),
                    "street_address": address_details.get("addressLine1"),
                    "postcode": address_details.get("postalCode"),
                    "city": address_details.get("cityName"),
                    "phone": contact_details.get("phone1"),
                    "email": contact_details.get("email"),
                    "website": store.get("dealerUrl"),
                    "lat": coordinates.get("latitude"),
                    "lon": coordinates.get("longitude"),
                    "opening_hours": oh,
                }
            )
