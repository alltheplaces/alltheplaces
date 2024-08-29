import scrapy

from locations.items import Feature


class MikuchaTHSpider(scrapy.Spider):
    name = "mikucha_th"
    item_attributes = {
        "brand_wikidata": "Q118640408",
        "brand": "Mikucha",
    }
    allowed_domains = [
        "mikucha.co.th",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    # Similar to HerronFoodsSpider
    def start_requests(self):
        yield scrapy.FormRequest(
            url="https://mikucha.co.th/wp-admin/admin-ajax.php",
            formdata={
                "action": "get_stores",
                "lat": "13.7563309",
                "lng": "100.5017651",
                "radius": "1000",
            },
            callback=self.parse,
        )

    def parse(self, response):
        stores = response.json()
        for i in range(0, len(stores)):
            store = stores[str(i)]

            properties = {
                "lat": store["lat"],
                "lon": store["lng"],
                "name": store["na"],
                "street_address": store["st"].strip(" ,"),
                "city": store["ct"].strip(),
                "postcode": store["zp"].strip(),
                "country": "TH",
                "website": store["gu"],
                "ref": store["ID"],
            }

            yield Feature(**properties)
