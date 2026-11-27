from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.react_server_components import parse_rsc


class LeonGBSpider(Spider):
    name = "leon_gb"
    item_attributes = {"brand": "LEON", "brand_wikidata": "Q6524851"}
    start_urls = ["https://leon.co/find-leon/?lat=51.5073044&lng=-0.1281113&zoom=14&type=all"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath("//*[contains(text(),'geoLocation')]/text()").getall()
        rsc = "".join(s for n, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        for location in DictParser.get_nested_key(dict(parse_rsc(rsc.encode())), "payload"):
            if location.get("geoLocation"):
                location.update(location.pop("locationDetails"))
                item = DictParser.parse(location)
                item["city"] = location.get("townOrCity")
                item["website"] = f'https://leon.co/restaurants/{location.get("slug")}/'
                apply_category(Categories.FAST_FOOD, item)
                yield item
