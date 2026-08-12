from typing import Any, Iterable

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsHKSpider(Spider):
    name = "mcdonalds_hk"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.com.hk"]
    start_urls = ["https://www.mcdonalds.com.hk/en/find-a-restaurant/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        objs = [
            chompjs.parse_js_object(s)
            for s in response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        ]
        data = dict(parse_rsc("".join([s for n, s in objs]).encode()))

        for store in DictParser.get_nested_key(data, "restaurants"):
            item = DictParser.parse(store)
            item["state"] = None
            item["ref"] = store["rid"]
            item["branch"] = item.pop("name")
            item["website"] = "https://www.mcdonalds.com.hk/en/find-a-restaurant/{}/".format(store["storeNo"])

            item["opening_hours"] = OpeningHours()
            for schedule in store["openingHours"]:
                for rule in schedule["hours"]:
                    if rule["start"] == "00:00" and rule["end"] == "00:00":
                        # The website renders this range as "Open 24 Hours", not as a closed day.
                        item["opening_hours"].add_range(rule["day"], "00:00", "24:00")
                    elif "$undefined" not in (rule["start"], rule["end"]):
                        item["opening_hours"].add_range(rule["day"], rule["start"], rule["end"])

            apply_category(Categories.FAST_FOOD, item)

            yield item
