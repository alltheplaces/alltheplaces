import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class CostaCoffeePLSpider(scrapy.Spider):
    name = "costacoffee_pl"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["costacoffee.pl"]
    start_urls = ["https://www.costacoffee.pl/api/cf/?content_type=storeLocatorStore&limit=1000"]
    no_refs = True

    def parse(self, response):
        data = response.json()['items']
        for store in data:
            properties = {
                "name": store['fields']["cmsLabel"],
                "addr_full": store['fields']["storeAddress"],
                "country": "PL",
                "lat": store['fields']['location']["lat"],
                "lon": store['fields']['location']["lon"],
            }

            apply_category(Categories.CAFE, properties)

            yield Feature(**properties)
