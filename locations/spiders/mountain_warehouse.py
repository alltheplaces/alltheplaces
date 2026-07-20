from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.react_server_components import parse_rsc


class MountainWarehouseSpider(Spider):
    name = "mountain_warehouse"
    item_attributes = {"brand": "Mountain Warehouse", "brand_wikidata": "Q6925414"}
    allowed_domains = ["www.mountainwarehouse.com"]
    start_urls = ["https://www.mountainwarehouse.com/stores/results/?search=all&lat=0&lng=0"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))

        for store in DictParser.get_nested_key(data, "AllStores"):
            store = {key: (None if value == "$undefined" else value) for key, value in store.items()}
            item = DictParser.parse(store)
            item["ref"] = store["Code"]
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([store.get("Address1"), store.get("Address2")])
            item["website"] = f"https://www.mountainwarehouse.com/stores/{store['Url']}/"

            item["opening_hours"] = OpeningHours()
            for hours in store.get("OpeningHours") or []:
                item["opening_hours"].add_ranges_from_string(
                    f"{hours['DayName']} {hours['OpenTime']}-{hours['CloseTime']}"
                )

            apply_category(Categories.SHOP_OUTDOOR, item)
            yield item
