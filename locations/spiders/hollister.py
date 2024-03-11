import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class HollisterSpider(scrapy.Spider):
    name = "hollister"
    item_attributes = {"brand": "Hollister", "brand_wikidata": "Q1257477"}
    allowed_domains = ["hollisterco.com"]
    start_urls = ["https://www.hollisterco.com/api/ecomm/h-us/storelocator/search?country="]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def parse(self, response):
        data = response.json()

        for row in data["physicalStores"]:
            properties = {
                "ref": row["storeNumber"],
                "name": row["name"],
                "country": row["country"],
                "state": row["stateOrProvinceName"],
                "city": row["city"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "phone": row["telephone"],
                "street_address": row["addressLine"][0],
                "postcode": row["postalCode"],
            }

            yield Feature(**properties)
