import scrapy
import json
from locations.items import GeojsonPointItem


class MenardsSpider(scrapy.Spider):
    name = "menards"
    item_attributes = {"brand": "Menards"}
    start_urls = ["https://www.menards.com/main/storeLocator.html"]
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"

    def parse(self, response):
        script = response.xpath(
            '//script[contains(., "initialStores")]/text()'
        ).extract_first()
        data = json.loads(
            script.extract_first().split("initialStores = ", 1)[1].rsplit(";\n", 1)[0]
        )

        for store in data:
            yield GeojsonPointItem(
                ref=store["number"],
                name=store["name"],
                addr_full=f"{store['street']} {store['city']}, {store['state']} {store['zip']}",
                postcode=store["zip"],
                city=store["city"],
                state=store["state"],
                lat=store["latitude"],
                lon=store["longitude"],
                website=f"https://www.menards.com/main/storeDetails.html?store={store['number']}",
            )
