import scrapy

from locations.user_agents import BROSWER_DEFAULT
from locations.items import GeojsonPointItem


class AbercrombieAndFitchSpider(scrapy.Spider):
    name = "abercrombie_and_fitch"
    item_attributes = {"brand": "Abercrombie & Fitch", "brand_wikidata": "Q319344"}
    allowed_domains = ["abercrombie.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
    user_agent = BROSWER_DEFAULT

    start_urls = [
        'https://www.abercrombie.com/api/ecomm/a-ca/storelocator/search?shopRegion=["US", "CA", "UK", "EU", "AM"]'
    ]

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

            for brand in row["physicalStoreAttribute"]:
                if brand["name"] == "Brand":
                    if brand["value"] == "ACF":
                        properties["brand"] = "Abercrombie & Fitch"
                        properties["brand_wikidata"] = "Q319344"
                    elif brand["value"] == "KID":
                        properties["brand"] = "Abercrombie Kids"
                        properties["brand_wikidata"] = "Q429856"

            yield GeojsonPointItem(**properties)
