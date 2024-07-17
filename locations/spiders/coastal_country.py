import scrapy

from locations.items import Feature


class CoastalCountrySpider(scrapy.Spider):
    name = "coastal_country"
    item_attributes = {"brand": "Coastal"}
    allowed_domains = ["www.coastalfarm.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ("https://www.coastalcountry.com/about/store-locations",)

    def parse(self, response):
        results = response.json()
        for data in results:
            properties = {
                "city": data["city"],
                "ref": data["id"],
                "lon": data["lng"],
                "lat": data["lat"],
                "addr_full": data["address"],
                "phone": data["phone"],
                "state": data["state"],
                "postcode": data["zip"],
                "website": data["url"],
            }

            yield Feature(**properties)
