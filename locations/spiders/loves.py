from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class LovesSpider(scrapy.Spider):
    name = "loves"
    SPEEDCO = {"brand": "Speedco", "brand_wikidata": "Q112455073"}
    item_attributes = {"brand": "Love's", "brand_wikidata": "Q1872496"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.loves.com/api/fetch_all_stores?requestingSite=Loves"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]:
            if store["isHotel"] is True:
                continue  # ChoiceHotelsSpider
            item = DictParser.parse(store)
            item["ref"] = store.get("number")
            item["website"] = "https://www.loves.com/locations/{}".format(store["number"])

            if "speedco" in store["mapPinUrl"].lower():
                item.update(self.SPEEDCO)
                apply_category(Categories.SHOP_TRUCK_REPAIR, item)
            else:
                apply_category({"highway": "services"}, item)
            yield item
