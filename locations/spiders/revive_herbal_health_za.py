import scrapy

from locations.items import Feature


class ReviveHerbalHealthZASpider(scrapy.Spider):
    name = "revive_herbal_health_za"
    item_attributes = {
        "brand_wikidata": "Q116498098",
        "brand": "Revive Herbal Health",
    }
    allowed_domains = [
        "reviveherbalhealth.co.za",
    ]

    def start_requests(self):
        yield scrapy.FormRequest(
            url="https://reviveherbalhealth.co.za/shop/wp-admin/admin-ajax.php",
            formdata={
                "action": "get_stores",
                "lat": "-29.679604756080494",
                "lng": "31.021939690785292",
                "radius": "600",
            },
            callback=self.parse,
        )

    # See also HeronFoods, Mikucha
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
                "country": "ZA",
                "website": store["gu"],
                "ref": store["ID"],
            }

            yield Feature(**properties)
