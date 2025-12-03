from typing import Any

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, OpeningHours


class LillyBGSpider(Spider):
    name = "lilly_bg"
    item_attributes = {"brand": "Lilly", "brand_wikidata": "Q111764460"}
    allowed_domains = ["www.lillydrogerie.bg"]
    start_urls = ["https://www.lillydrogerie.bg/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "window.stenikShopShopsData =")]/text()').get()
        ):
            location["latitude"] = location["latitude"].replace(",", "")
            location["longitude"] = location["longitude"].replace(",", "")
            item = DictParser.parse(location)
            item["ref"] = location["id"]
            item["addr_full"] = None
            item["street_address"] = item.pop("name")
            item["phone"] = location["mobilephone"]
            hours_string = " ".join(filter(None, Selector(text=location["worktime"]).xpath("//p/text()").getall()))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string, DAYS_BG)
            apply_category(Categories.SHOP_CHEMIST, item)
            yield item
