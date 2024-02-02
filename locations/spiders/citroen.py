import re

import scrapy

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_EN, DAYS_FR, DAYS_NL, DAYS_SE, OpeningHours, sanitise_day
from locations.items import Feature


class CitroenSpider(scrapy.Spider):
    name = "citroen"
    item_attributes = {"brand": "Citroen", "brand_wikidata": "Q6746"}
    start_urls = [
        "https://www.citroen.co.uk/apps/atomic/DealersServlet?path=L2NvbnRlbnQvY2l0cm9lbi93b3JsZHdpZGUvdWsvZW4%3D&searchType=latlong",
        "https://www.citroen.be/apps/atomic/DealersServlet?distance=30000&latitude=50.84439&longitude=4.35608&maxResults=1000&orderResults=false&path=L2NvbnRlbnQvY2l0cm9lbi93b3JsZHdpZGUvYmVsZ2l1bS9mcl9mcg%3D%3D&searchType=latlong",
        "https://www.citroen.nl/apps/atomic/DealersServlet?distance=300&latitude=52.36993&longitude=4.90787&maxResults=40&orderResults=false&path=L2NvbnRlbnQvY2l0cm9lbi93b3JsZHdpZGUvbmV0aGVybGFuZHMvbmw=&searchType=latlong",
        "https://www.citroen.se/apps/atomic/DealersServlet?distance=300&latitude=59.33257&longitude=18.06682&maxResults=40&orderResults=false&path=L2NvbnRlbnQvY2l0cm9lbi93b3JsZHdpZGUvc3dlZGVuL3Nl&searchType=latlong",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

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
                    day = sanitise_day(day, {**DAYS_NL, **DAYS_FR, **DAYS_SE, **DAYS_EN})
                    for hours in hours.split(" "):
                        if "-" in hours:
                            try:
                                start, end = hours.split("-", maxsplit=1)
                                oh.add_range(day, start, end, time_format="%H:%M")
                            except:
                                pass

            item = Feature(
                {
                    "ref": store.get("rrdi"),
                    "name": store.get("dealerName"),
                    "street_address": address_details.get("addressLine1"),
                    "postcode": address_details.get("postalCode"),
                    "city": address_details.get("cityName"),
                    "country": re.findall(r"\.[a-z]{2}/", response.url)[0][1:3].upper(),
                    "phone": contact_details.get("phone1"),
                    "email": contact_details.get("email"),
                    "website": store.get("dealerUrl"),
                    "lat": coordinates.get("latitude"),
                    "lon": coordinates.get("longitude"),
                    "opening_hours": oh,
                }
            )

            services = str(store.get("services"))
            car_dealer = re.findall("'type': 'sales'", services)
            car_repair = re.findall("'type': 'service'", services)
            if len(car_dealer) > 0 and len(car_repair) > 0:
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no("service:vehicle:car_repair", item, True)
            elif car_dealer:
                apply_category(Categories.SHOP_CAR, item)
            elif car_repair:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            else:
                apply_category(Categories.SHOP_CAR, item)

            yield item
