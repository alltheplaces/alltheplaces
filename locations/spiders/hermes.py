import json

import scrapy

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class HermesSpider(scrapy.Spider):
    name = "hermes"
    item_attributes = {
        "brand": "Hermès",
        "brand_wikidata": "Q843887",
    }
    allowed_domains = ["hermes.com"]
    start_urls = ["https://www.hermes.com/us/en/find-store/"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response):
        raw_data = DictParser.get_nested_key(
            json.loads(response.xpath('//*[@id="hermes-state"]/text()').get()), "shops"
        )
        for store in raw_data:
            if store.get("geoCoordinates"):
                store.update(store.pop("geoCoordinates"))
            item = DictParser.parse(store)
            item["branch"] = store["shortTitle"].replace("Hermès ", "")
            item["street_address"] = store["streetAddress1"]
            item["ref"] = store.get("shopId")
            item["website"] = f'https://www.hermes.com/uk/en/{store["url"]}'
            yield item
