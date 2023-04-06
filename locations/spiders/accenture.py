import scrapy
from scrapy.http import JsonRequest

from locations.items import Feature


class AccentureSpider(scrapy.Spider):
    name = "accenture"
    item_attributes = {"brand": "Accenture", "brand_wikidata": "Q29123313"}
    allowed_domains = ["accenture.com"]
    start_urls = ["https://www.accenture.com/us-en/about/location-index"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True

    def parse(self, response, **kwargs):
        for country in response.xpath('//li[@class="cmp-link-teaser__list-item"]/a/text()').getall():
            yield JsonRequest(
                url=f"https://www.accenture.com/api/sitecore/LocationsHeroModule/GetLocation?query={country}&from=0&size=10000&language=en",
                callback=self.parse_country,
            )

    def parse_country(self, response, **kwargs):
        for store_data in response.json()["documents"]:
            properties = {
                "name": store_data["LocationName"],
                "street_address": store_data["Address"],
                "image": store_data["ExternalImageURL"],
                "city": store_data["CityName"],
                "state": store_data["StateCode"],
                "postcode": store_data["PostalZipCode"],
                "country": store_data["Country"],
                "phone": store_data.get("ContactTel"),
                "lat": float(store_data["Latitude"]),
                "lon": float(store_data["Longitude"]),
                "website": store_data.get("LocationURL"),
            }

            yield Feature(**properties)
