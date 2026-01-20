import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class PeugeotSpider(scrapy.Spider):
    name = "peugeot"
    start_urls = [
        "https://www.peugeot.se/apps/atomic/DealersServlet?distance=30000&latitude=59.33257&longitude=18.06682&maxResults=4000&orderResults=false&path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvc3dlZGVuL3Nl&searchType=latlong",
        "https://www.peugeot.cz/apps/atomic/DealersServlet?distance=300&latitude=50.07914&longitude=14.43299&maxResults=40000&orderResults=false&path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvY3plY2hfcmVwdWJsaWMvY3o%3D&searchType=latlong",
        "https://www.peugeot.es/apps/atomic/DealersServlet?distance=300&latitude=40.41955&longitude=-3.69197&maxResults=40&orderResults=false&path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvc3BhaW4vZXM%3D&searchType=latlong",
        "https://www.peugeot.nl/apps/atomic/DealersServlet?distance=30000&latitude=52.36993&longitude=4.90787&maxResults=40000&orderResults=false&path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvbmV0aGVybGFuZHMvbmw%3D&searchType=latlong",
        "https://www.peugeot.fr/apps/atomic/DealersServlet?path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvZnJhbmNlL2ZyX2Zy&searchType=latlong",
        "https://www.peugeot.com.my/apps/atomic/DealersServlet?path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvbWFsYXlzaWEvZW4%3D&searchType=latlong",
        "https://www.peugeot-eg.com/apps/atomic/DealersServlet?path=L2NvbnRlbnQvcGV1Z2VvdC93b3JsZHdpZGUvZWd5cHQvZW4%3D&searchType=latlong",
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
            for service_type in store["services"]:
                if service_type["name"] in [
                    "New Vehicles",
                    "Prodej nových vozů",
                    "Venta de Vehículos Turismos",
                    "Nieuwe auto's",
                    "Venta de Vehículos Turismos",
                    "VENTES DE VÉHICULES NEUFS",
                ]:
                    sales_item = item.deepcopy()
                    sales_item["ref"] = sales_item["ref"] + "-SALES"
                    apply_category(Categories.SHOP_CAR, sales_item)
                    yield sales_item
                elif service_type["name"] in [
                    "Aftersales",
                    "Autorizovaný servis",
                    "Servicio Oficial Turismos",
                    "Après-vente",
                ]:
                    service_item = item.deepcopy()
                    service_item["ref"] = service_item["ref"] + "-SERVICE"
                    apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                    yield service_item
                elif service_type["name"] in [
                    "Parts",
                    "dílů",
                    "Pieza de recambio",
                ]:
                    spare_parts_item = item.deepcopy()
                    spare_parts_item["ref"] = spare_parts_item["ref"] + "-SPARE_PARTS"
                    apply_category(Categories.SHOP_CAR_PARTS, spare_parts_item)
                    yield spare_parts_item
