import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class DiSpider(scrapy.Spider):
    name = "di"
    item_attributes = {
        "brand": "Di",
    }
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "x-http-method-override": "GET",
            "content-type": "application/json",
            "Accept": "*/*",
        },
    }

    def start_requests(self):
        yield JsonRequest(
            url="https://www.di.be/ajax.V1.php/fr_FR/Rbs/Storelocator/Store/",
            data={
                "websiteId": 100187,
                "sectionId": 9416724,
                "pageId": 1967981,
                "data": {
                    "currentStoreId": 0,
                    "distanceUnit": "kilometers",
                    "distance": "1000kilometers",
                    "coordinates": {"latitude": 50.63295859999999, "longitude": 5.569749799999999},
                    "commercialSign": 0,
                },
                "dataSets": "coordinates,address,card,allow",
                "URLFormats": "canonical,contextual",
                "visualFormats": "original,listItem",
                "pagination": "0,500",
                "referer": "https://www.di.be/fr/magasins.html",
            },
            method="POST",
        )

    def parse(self, response):
        stores = response.json()
        for store in stores.get("items"):
            store_details = store.get("common")
            address_details = store.get("address").get("fields")
            coordinates = store.get("coordinates")
            contact_details = store.get("card")
            item = Feature(
                ref=store_details.get("id"),
                name=store_details.get("title"),
                website=store_details.get("URL").get("canonical"),
                street=address_details.get("street"),
                housenumber=address_details.get("houseCode"),
                postcode=address_details.get("zipCode"),
                city=address_details.get("locality"),
                country=address_details.get("countryCode"),
                addr_full=", ".join(
                    filter(
                        None,
                        [
                            address_details.get("houseCode"),
                            address_details.get("street"),
                            address_details.get("locality"),
                            address_details.get("zipCode"),
                        ],
                    )
                ),
                lat=coordinates.get("latitude"),
                lon=coordinates.get("longitude"),
                email=contact_details.get("email"),
                phone=contact_details.get("phone"),
            )
            apply_category(Categories.SHOP_COSMETICS, item)
            yield item
