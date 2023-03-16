import scrapy

from locations.items import Feature


class HemmakvallSESpider(scrapy.Spider):
    name = "hemmakvall_se"

    item_attributes = {"brand": "Hemmakväll", "brand_wikidata": "Q10521791"}

    def start_requests(self):
        yield scrapy.http.FormRequest(
            url="https://www.hemmakvall.se/wp-admin/admin-ajax.php",
            formdata={
                "action": "csl_ajax_onload",
                "address": "",
                "formdata": "addressInput=",
                "lat": "60.128161",
                "lng": "18.643501",
                "radius": "15000",
            },
        )

    def parse(self, response, **kwargs):
        for store in response.json().get("response"):
            yield Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("name"),
                    "street_address": store.get("street_address"),
                    "addr_full": " ".join(
                        filter(None, [store.get("address"), store.get("address2"), store.get("city"), store.get("zip")])
                    ),
                    "lat": store.get("lat"),
                    "lon": store.get("lng"),
                    "website": store.get("url"),
                    "email": store.get("email"),
                    "phone": store.get("phone"),
                    "postcode": store.get("zip"),
                    "city": store.get("city"),
                    "state": store.get("state"),
                }
            )
