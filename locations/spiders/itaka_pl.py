from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.react_server_components import parse_rsc


class ItakaPLSpider(Spider):
    name = "itaka_pl"
    item_attributes = {"brand": "Itaka", "brand_wikidata": "Q16560452"}
    start_urls = ["https://www.itaka.pl/biura/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))

        for office in DictParser.get_nested_key(data, "initialSalesOffices"):
            item = DictParser.parse(office)
            item["ref"] = str(office["id"])
            item["street_address"] = item.pop("addr_full", None)
            if office_website := office.get("website"):
                item["website"] = f"https://www.itaka.pl/{office_website}"
            if (main_image := office.get("mainImage")) and main_image.get("url"):
                item["image"] = main_image["url"]
            item["opening_hours"] = OpeningHours()
            for day, hours in (office.get("openingHours") or {}).items():
                if (day_code := sanitise_day(day)) and hours.get("from") and hours.get("to"):
                    item["opening_hours"].add_range(day_code, hours["from"], hours["to"])
            item.pop("name", None)
            apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
            yield item
