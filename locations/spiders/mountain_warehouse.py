from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
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
            item = Feature()
            item["ref"] = store["Code"]
            item["lat"] = store["Lat"]
            item["lon"] = store["Long"]
            item["branch"] = store["StoreName"]
            item["street_address"] = store["Address1"]
            if (addr2 := store.get("Address2")) and addr2 != "$undefined":
                item["street_address"] += ", " + addr2
            item["city"] = store.get("City")
            item["postcode"] = store.get("PostCode")
            item["phone"] = store.get("Phone")
            item["website"] = f"https://www.mountainwarehouse.com/stores/{store['Url']}/"

            item["opening_hours"] = OpeningHours()
            for hours in store.get("OpeningHours", []):
                item["opening_hours"].add_ranges_from_string(
                    f"{hours['DayName']} {hours['OpenTime']}-{hours['CloseTime']}"
                )

            apply_category(Categories.SHOP_OUTDOOR, item)
            yield item
