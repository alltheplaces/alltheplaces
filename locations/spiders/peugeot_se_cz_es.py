import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class PeugeotSECZESSpider(scrapy.Spider):
    name = "peugeot_se_cz_es"
    start_urls = [
        "https://www.peugeot.se/apps/atomic/DealersServlet?distance=30000&latitude=59.33257&longitude=18.06682&maxResults=4000&orderResults=false&path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvc3dlZGVuL3Nl&searchType=latlong",
        "https://www.peugeot.cz/apps/atomic/DealersServlet?distance=300&latitude=50.07914&longitude=14.43299&maxResults=40000&orderResults=false&path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvY3plY2hfcmVwdWJsaWMvY3o%3D&searchType=latlong",
        "https://www.peugeot.es/apps/atomic/DealersServlet?distance=300&latitude=40.41955&longitude=-3.69197&maxResults=40&orderResults=false&path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvc3BhaW4vZXM%3D&searchType=latlong",
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

            service_names = []
            for service in store.get("services", []):
                service_names.append(service.get("name"))

            if any(
                s in service_names
                for s in (
                    "New Vehicles",
                    "Prodej nových vozů",
                    "Venta de Vehículos Comerciales",
                    "Venta de Vehículos Turismos",
                )
            ):
                apply_category(Categories.SHOP_CAR, item)
            elif any(
                s in service_names
                for s in (
                    "Aftersales",
                    "Autorizovaný servis",
                    "Servicio Oficial Turismos",
                )
            ):
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            elif any(
                s in service_names
                for s in (
                    "Parts",
                    "dílů",
                    "Pieza de recambio",
                )
            ):
                apply_category(Categories.SHOP_CAR_PARTS, item)

            yield item
