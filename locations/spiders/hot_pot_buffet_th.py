import json

import scrapy

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class HotPotBuffetTHSpider(scrapy.Spider):
    name = "hot_pot_buffet_th"
    item_attributes = {
        "brand": "HOT POT Buffet",
        "brand_wikidata": "Q125919341",
    }
    allowed_domains = ["hermes.com"]
    start_urls = ["http://www.hotpotmember.com/branch/search"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response):
        data_js = json.loads(
            response.xpath('//body/script[contains(text(), "__INITIAL_STATE__")]/text()')
            .get()
            .split("__INITIAL_STATE__=", 1)[1]
        )
        for brand_item in data_js.get("branch").get("all"):
            if brand_item.get("category") == "Hot Pot Inter Buffet":
                for store in brand_item.get("branch"):
                    item = DictParser.parse(store)
                    item["name"] = "HOT POT Buffet"
                    item["phone"] = store.get("mobile")

                    yield item
