import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

CHECKERS = {"brand": "Checkers", "brand_wikidata": "Q63919315"}
RALLYS = {"brand": "Rally's", "brand_wikidata": "Q63919323"}


class CheckersAndRallysUSSpider(Spider):
    name = "checkers_and_rallys_us"
    start_urls = ["https://checkersandrallys.com/unified-gateway/online-ordering/v1/all-stores/8159"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores_v1"]:
            if location["name"] in ("Checkers - POS Test Store", "Checkers Drive-In Restaurants (demo)"):
                continue
            item = DictParser.parse(location["address"])
            item["name"] = None
            item["street_address"] = item.pop("street")
            item["addr_full"] = location["address"]["formatted_address"]

            if m := re.match(r"^(Checkers|Rally's) ?\((\d+)\)(.+)?$", location["name"]):
                if m.group(1) == "Checkers":
                    item.update(CHECKERS)
                elif m.group(1) == "Rally's":
                    item.update(RALLYS)
                item["ref"] = m.group(2)
            else:
                self.logger.error("Unexpected location: {}".format(location["name"]))

            apply_category(Categories.FAST_FOOD, item)

            yield item
