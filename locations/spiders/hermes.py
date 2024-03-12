import scrapy

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class HermesSpider(scrapy.Spider):
    name = "hermes"
    item_attributes = {
        "brand": "Hermes",
        "brand_wikidata": "Q843887",
    }
    allowed_domains = ["hermes.com"]
    start_urls = ["https://bck.hermes.com/stores?lang=en"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response):
        for store in response.json().get("shops"):
            store["location"] = store.pop("geoCoordinates")
            item = DictParser.parse(store)
            item["ref"] = store.get("shopId")
            item["website"] = f'https://www.hermes.com/uk/en/{store["url"]}'

            yield item
