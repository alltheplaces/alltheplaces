import scrapy

from locations.items import Feature


class PeugeotSESpider(scrapy.Spider):
    name = "peugeot_se"
    start_urls = [
        "https://www.peugeot.se/apps/atomic/DealersServlet?distance=30000&latitude=59.33257&longitude=18.06682&maxResults=4000&orderResults=false&path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvc3dlZGVuL3Nl&searchType=latlong"
    ]

    item_attributes = {"brand": "Peugeot", "brand_wikidata": "Q6742"}

    def parse(self, response, **kwargs):
        for store in response.json().get("payload").get("dealers"):
            address_details = store.get("address")
            coordinates = store.get("geolocation")
            contact_details = store.get("generalContact")
            yield Feature(
                {
                    "ref": store.get("rrdi"),
                    "name": store.get("dealerName"),
                    "street_address": address_details.get("addresssLine1"),
                    "phone": contact_details.get("phone1"),
                    "email": contact_details.get("email"),
                    "postcode": address_details.get("postalCode"),
                    "city": address_details.get("cityName"),
                    "state": address_details.get("county"),
                    "website": store.get("dealerUrl"),
                    "lat": float(coordinates.get("latitude")),
                    "lon": float(coordinates.get("longitude")),
                }
            )
