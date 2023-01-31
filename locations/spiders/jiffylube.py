import scrapy

from locations.items import Feature


class JiffyLubeSpider(scrapy.Spider):
    name = "jiffylube"
    item_attributes = {"brand": "Jiffy Lube", "brand_wikidata": "Q6192247"}
    allowed_domains = ["www.jiffylube.com"]
    start_urls = ("https://www.jiffylube.com/api/locations",)

    def parse(self, response):
        stores = response.json()

        for store in stores:
            store_url = "https://www.jiffylube.com/api" + store["_links"]["_self"]
            yield scrapy.Request(store_url, callback=self.parse_store)

    def parse_store(self, response):
        store_data = response.json()

        properties = {
            "ref": store_data["id"],
            "street_address": store_data["address"],
            "city": store_data["city"],
            "state": store_data["state"],
            "postcode": store_data["postal_code"].strip(),
            "country": store_data["country"],
            "phone": store_data["phone_main"],
            "lat": float(store_data["coordinates"]["latitude"]),
            "lon": float(store_data["coordinates"]["longitude"]),
            "website": "https://www.jiffylube.com" + store_data["_links"]["_self"],
        }

        yield Feature(**properties)
