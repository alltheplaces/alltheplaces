from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.arbys_us import ArbysUSSpider
from locations.spiders.aw_restaurants import AwRestaurantsSpider
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.spiders.ljsilvers import LjsilversSpider
from locations.spiders.sonic_drivein import SonicDriveinSpider
from locations.spiders.taco_bell_us import TACO_BELL_SHARED_ATTRIBUTES
from locations.spiders.walmart_us import WalmartUSSpider

brands_map = {
    "KA": [KFC_SHARED_ATTRIBUTES, AwRestaurantsSpider.item_attributes],
    "KB": [KFC_SHARED_ATTRIBUTES, TACO_BELL_SHARED_ATTRIBUTES],
    "KFC": [KFC_SHARED_ATTRIBUTES],
    "KL": [KFC_SHARED_ATTRIBUTES, LjsilversSpider.item_attributes],
    "KT": [KFC_SHARED_ATTRIBUTES, TACO_BELL_SHARED_ATTRIBUTES],
    "KW": [KFC_SHARED_ATTRIBUTES, WalmartUSSpider.item_attributes],
    "Sonic": [SonicDriveinSpider.item_attributes],
    "Arbys": [ArbysUSSpider.item_attributes],
    "TB": [TACO_BELL_SHARED_ATTRIBUTES],
}


class KbpFoodsUSSpider(Spider):
    name = "kbp_foods_us"
    start_urls = ["https://kbpbrands.com/api/locations"]
    item_attributes = {"operator": "KBP Foods"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            apply_category(Categories.FAST_FOOD, item)
            if brands := brands_map.get(store["type"].strip()):
                for b in brands:
                    i = item.deepcopy()
                    i["ref"] = "{}-{}".format(item["ref"], b["brand"])
                    i.update(b)
                    yield i
            else:
                self.logger.error("Unmapped brand: {}".format(store["type"]))
                yield item
