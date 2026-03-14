import json
from typing import Any
from urllib.parse import urljoin

import chompjs
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

TBS = {"brand_wikidata": "Q16953670"}
RA = {"name": "Red Apple", "brand": "Red Apple"}


class TheBargainShopCASpider(CrawlSpider):
    name = "the_bargain_shop_ca"
    start_urls = ["https://www.thebargainshop.com/stores.htm"]
    rules = [Rule(LinkExtractor(r"thebargainshop.com/store/(\d+)/$"), "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "google_structured_data")]/text()').get()
        )

        if "soci" not in data["meta"]:
            return

        location = json.loads(data["meta"]["soci"])
        item = DictParser.parse(location)
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("addr_full")
        item["facebook"] = location["facebook"]

        item["opening_hours"] = self.parse_opening_hours(location["hours"])

        for role in data["roles"]:
            if role["role"] == "tbs":
                item.update(TBS)
                item["website"] = urljoin("https://www.thebargainshop.com", data["link"])
                break
            elif role["role"] == "ra":
                item.update(RA)
                apply_category(Categories.SHOP_VARIETY_STORE, item)
                item["website"] = urljoin("https://www.redapplestores.com", data["link"])
                break
        else:
            self.logger.error("Unknown format")

        yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, times in rules.items():
            for time in times:
                oh.add_range(day, *time.split("-"))
        return oh
