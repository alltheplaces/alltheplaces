import scrapy

from locations.items import Feature


class HungryJacksSpider(scrapy.Spider):
    name = "hungry_jacks"
    item_attributes = {"brand": "Hungry Jack's", "brand_wikidata": "Q3036373"}
    allowed_domains = ["hungryjacks.com.au"]
    start_urls = [
        "https://www.hungryjacks.com.au/api/storelist",
    ]

    def parse(self, response):
        data = response.json()

        for i in data:
            properties = {
                "ref": i["store_id"],
                "name": i["name"],
                "street_address": i["location"]["address"],
                "city": i["location"]["suburb"],
                "state": i["location"]["state"],
                "postcode": i["location"]["postcode"],
                "country": "AU",
                "phone": i["location"]["phone"],
                "lat": i["location"]["lat"],
                "lon": i["location"]["long"],
            }

            yield Feature(**properties)
