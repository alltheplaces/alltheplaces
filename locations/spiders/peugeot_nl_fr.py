import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class PeugeotNLFRSpider(scrapy.Spider):
    name = "peugeot_nl_fr"
    start_urls = [
        "https://www.peugeot.nl/apps/atomic/DealersServlet?distance=30000&latitude=52.36993&longitude=4.90787&maxResults=40000&orderResults=false&path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvbmV0aGVybGFuZHMvbmw%3D&searchType=latlong",
        "https://www.peugeot.fr/apps/atomic/DealersServlet?path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvZnJhbmNlL2ZyX2Zy&searchType=latlong",
    ]

    item_attributes = {"brand": "Peugeot", "brand_wikidata": "Q6742"}

    def parse(self, response, **kwargs):
        for store in response.json().get("payload").get("dealers"):
            address_details = store.get("address")
            coordinates = store.get("geolocation")
            contact_details = store.get("generalContact")
            item = Feature(
                {
                    "ref": store.get("siteGeo"),
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
            apply_category(Categories.SHOP_CAR, item)
            yield item
