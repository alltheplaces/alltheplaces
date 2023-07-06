import scrapy

from locations.items import Feature


class MonclerSpider(scrapy.Spider):
    name = "moncler"
    item_attributes = {"brand": "Moncler", "brand_wikidata": "Q1548951"}
    allowed_domains = ["moncler.com"]
    start_urls = ["https://www.moncler.com/on/demandware.store/Sites-MonclerEU-Site/it_IT/StoresApi-FindAll"]
    requires_proxy = True

    def parse(self, response):
        data = response.json()
        for i in data["stores"]:
            properties = {
                "ref": i["ID"],
                "name": i["name"],
                "street_address": i["address1"],
                "city": i["city"],
                "postcode": i.get("postalCode"),
                "country": i["countryCode"]["value"],
                "phone": i["phone"],
                "lat": i["latitude"],
                "lon": i["longitude"],
            }

            yield Feature(**properties)
