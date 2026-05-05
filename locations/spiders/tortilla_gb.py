from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.react_server_components import parse_rsc


class TortillaGBSpider(Spider):
    name = "tortilla_gb"
    item_attributes = {"brand": "Tortilla", "brand_wikidata": "Q21006828"}
    allowed_domains = ["www.tortilla.co.uk"]
    start_urls = ["https://www.tortilla.co.uk/restaurants"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))

        for store in DictParser.get_nested_key(data, "restaurants"):
            content = store.get("content")
            item = DictParser.parse(content)

            item["ref"] = store.get("full_slug")
            item["branch"] = item.pop("name")
            item["website"] = f"https://www.tortilla.co.uk/restaurants/{store.get('slug')}"

            apply_yes_no(Extras.INDOOR_SEATING, item, "eat-in" in content.get("options"))
            apply_yes_no(Extras.TAKEAWAY, item, "takeaway" in content.get("options"))
            apply_yes_no(Extras.DELIVERY, item, "delivery" in content.get("options"))
            apply_yes_no(Extras.WHEELCHAIR, item, "wheelchair-accessible" in content.get("options"))

            apply_category(Categories.FAST_FOOD, item)
            yield item
