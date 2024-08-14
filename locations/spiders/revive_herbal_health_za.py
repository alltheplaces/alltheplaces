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
                "action": "get_all_stores",
                "lat": "",
                "lng": "",
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

            if "te" in store:
                properties["phone"] = store["te"]
            elif "mo" in store:
                properties["phone"] = store["mo"]

            yield Feature(**properties)
