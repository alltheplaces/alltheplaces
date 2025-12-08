from copy import deepcopy

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaUSSpider(scrapy.Spider):
    name = "mazda_us"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    start_urls = ["https://www.mazdausa.com/handlers/dealer.ajax"]

    def parse(self, response, **kwargs):
        if dealers := response.json()["body"]["results"]:
            for dealer in dealers:
                item = DictParser.parse(dealer)
                item["website"] = dealer.get("webUrl")
                item["phone"] = dealer.get("dayPhone")

                shop_item = deepcopy(item)
                apply_category(Categories.SHOP_CAR, shop_item)
                yield shop_item

                if dealer.get("serviceUrl"):
                    service_item = deepcopy(item)
                    service_item["ref"] = f"{item['ref']}-SERVICE"
                    apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                    yield service_item

            current_page = kwargs.get("page", 1)

            yield JsonRequest(url=f"{self.start_urls[0]}?p={current_page + 1}", cb_kwargs=dict(page=current_page + 1))
