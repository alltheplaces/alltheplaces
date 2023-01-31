import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class AbercrombieAndFitchSpider(scrapy.Spider):
    name = "abercrombie_and_fitch"
    item_attributes = {"brand": "Abercrombie & Fitch", "brand_wikidata": "Q319344"}
    allowed_domains = ["abercrombie.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
    user_agent = BROWSER_DEFAULT

    start_urls = [
        "https://www.abercrombie.com/api/ecomm/a-uk/storelocator/search?country=US",
        "https://www.abercrombie.com/api/ecomm/a-uk/storelocator/search?country=CA",
        "https://www.abercrombie.com/api/ecomm/a-uk/storelocator/search?country=UK",
        "https://www.abercrombie.com/api/ecomm/a-uk/storelocator/search?country=EU",
        "https://www.abercrombie.com/api/ecomm/a-uk/storelocator/search?country=AM",
    ]

    def parse(self, response):
        data = response.json()
        
        if data["physicalStores"] is None:
            return

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

            for brand in row["physicalStoreAttribute"]:
                if brand["name"] == "Brand":
                    if brand["value"] == "ACF":
                        properties["brand"] = "Abercrombie & Fitch"
                        properties["brand_wikidata"] = "Q319344"
                    elif brand["value"] == "KID":
                        properties["brand"] = "Abercrombie Kids"
                        properties["brand_wikidata"] = "Q429856"

            yield Feature(**properties)
