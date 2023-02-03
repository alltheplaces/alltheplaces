import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class McCollsGBSpider(scrapy.Spider):
    name = "mccolls_gb"
    MCCOLLS = {"brand": "McColl's","brand_wikidata": "Q16997477"}
    MARTINS = {"brand": "Martin's","brand_wikidata": "Q16997477"}
    RSMCCOLL = {"brand": "RS McColl","brand_wikidata": "Q7277785"}
    MORRISONS_DAILY = {"brand": "Morrisons Daily","brand_wikidata": "Q99752411"}
    item_attributes = MCCOLLS
    start_urls = ["https://www.mccolls.co.uk/storelocator/"]

    def parse(self, response):
        script = json.loads(response.xpath('//script[contains(., "allStores")]/text()').get())
        for store in DictParser.get_nested_key(script, "items"):
            item = DictParser.parse(store)
            item["website"] = store["store_url"]
            item["street_address"] = store.get("address")
            item["addr_full"] = ", ".join(filter(None,[store.get("address"),store.get("address_1"),store.get("address_2"),store.get("address_3"),store.get("town"),store.get("county"),store.get("zip")]))

            if store["trading_name"] == "MORRISONS DAILY":
                item.update(self.MORRISONS_DAILY)
            elif store["trading_name"] == "MARTINS":
                item.update(self.MARTINS)
            elif store["trading_name"] == "RS MCCOLL":
                item.update(self.RSMCCOLL)

            if store["store_type"] == "NEWSAGENT":
                apply_category(Categories.SHOP_NEWSAGENT, item)
            elif store["store_type"] == "CONVENIENCE":
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif store["store_type"] == "CONVENIENCE PLUS":
                apply_category(Categories.SHOP_CONVENIENCE, item)

            # TODO: parse opening hours from the store JSON
            yield item
