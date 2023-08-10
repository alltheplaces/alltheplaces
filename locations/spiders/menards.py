import json

import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class MenardsSpider(scrapy.Spider):
    name = "menards"
    item_attributes = {"brand": "Menards", "brand_wikidata": "Q1639897"}
    start_urls = ["https://www.menards.com/store-details/locator.html"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        data = json.loads(response.xpath("//@data-initial-stores").get())

        for store in data:
            yield Feature(
                ref=store["number"],
                name=store["name"],
                addr_full=f"{store['street']}, {store['city']}, {store['state']} {store['zip']}",
                street_address=store["street"],
                postcode=store["zip"],
                city=store["city"],
                state=store["state"],
                lat=store["latitude"],
                lon=store["longitude"],
                website=f"https://www.menards.com/main/storeDetails.html?store={store['number']}",
            )
