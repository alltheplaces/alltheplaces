from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class HellenicBankCYSpider(Spider):
    name = "hellenic_bank_cy"
    item_attributes = {"brand_wikidata": "Q5707160"}
    start_urls = ["https://www.hellenicbank.com/el/personal/locations"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "storesData")]/text()').get()
        )["records"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["city"] = location["address"]["additions"]["town"]
            item["extras"]["fax"] = location["additions"]["contactDetailsFax"]
            if location["placeType"] == "ATM":
                apply_category(Categories.ATM, item)
            elif location["placeType"] == "BRANCH":
                apply_category(Categories.BANK, item)

            yield item
