import scrapy

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class AnthropologieSpider(scrapy.Spider):
    name = "anthropologie"
    item_attributes = {"brand": "Anthropologie", "brand_wikidata": "Q4773903"}
    start_urls = [
        "https://www.anthropologie.com/api/misl/v1/stores/search?brandId=54%7C04",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response, **kwargs):
        for store in response.json()["results"]:
            item = DictParser.parse(store)
            item["name"] = store.get("addresses").get("marketing").get("name") + "- Anthropologie Store"
            item["lon"], item["lat"] = store.get("loc")[0], store.get("loc")[1]
            if address2 := store.get("addressLineTwo"):
                item["addr_full"] = ",".join([item["street_address"], address2])
            yield item
