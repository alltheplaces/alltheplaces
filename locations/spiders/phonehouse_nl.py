import scrapy
from scrapy import FormRequest

from locations.items import Feature


class PhoneHouseNLSpider(scrapy.Spider):
    name = "phonehouse_nl"
    item_attributes = {"brand": "Phone House", "brand_wikidata": "Q325113"}
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "x-requested-with": "XMLHttpRequest",
            "accept": "application/json, text/javascript, */*; q=0.01",
        }
    }

    def start_requests(self):
        yield FormRequest(
            url="https://www.phonehouse.nl/retainable/stores/find",
        )

    def parse(self, response):
        for store in response.json().get("stores"):
            address = store.get("address")
            yield Feature(
                {
                    "ref": store.get("id"),
                    "housenumber": address.get("HouseNumber"),
                    "street_address": " ".join([address.get("HouseNumber"), address.get("Street")]),
                    "addr_full": " ".join(
                        [address.get("HouseNumber"), address.get("Street"), address.get("City"), address.get("ZipCode")]
                    ),
                    "postcode": address.get("ZipCode"),
                    "city": address.get("City"),
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                }
            )
