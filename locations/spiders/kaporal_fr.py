from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class KaporalFRSpider(Spider):
    name = "kaporal_fr"
    item_attributes = {"brand": "Kaporal", "brand_wikidata": "Q125660181"}
    start_urls = ["https://www.kaporal.com/fr_fr/shops"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for key, obj in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "__APOLLO_STATE__")]/text()').get()
        ).items():
            # if not key.startswith("KaporalShop"):
            #    continue
            if obj["__typename"] != "KaporalShop":
                continue
            item = DictParser.parse(obj)
            item["website"] = item["extras"]["website:fr"] = "https://www.kaporal.com/fr_fr{}".format(obj["url"])
            item["extras"]["website:en"] = "https://www.kaporal.com/en_fr{}".format(obj["url"])

            item["branch"] = item.pop("name").removeprefix("KAPORAL STORE ")
            if item["branch"].startswith("OUTLET "):
                item["branch"] = item["branch"].removeprefix("OUTLET ")
                item["extras"]["factory_outlet"] = "yes"

            yield item
