import re
from typing import Any
from urllib.parse import urljoin

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.react_server_components import parse_rsc


class LeosLeklandSESpider(Spider):
    name = "leos_lekland_se"
    item_attributes = {"brand": "Leo's Lekland", "brand_wikidata": "Q133225932"}
    allowed_domains = ["leoslekland.se"]
    start_urls = ["https://www.leoslekland.se/lekland"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))

        for location in DictParser.get_nested_key(data, "playcenters"):
            addr = location["address"]
            item = Feature()
            item["ref"] = location["backendSlug"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["website"] = urljoin("https://www.leoslekland.se/lekland/", location["backendSlug"])
            item["branch"] = location["name"]
            if addr:
                item["addr_full"] = addr.strip()
                if m := re.match(r"^(.+?),?\s*(\d{3}\s*\d{2})\s+(.+)$", item["addr_full"]):
                    item["street_address"] = m.group(1).strip()
                    item["postcode"] = re.sub(r"\s+", " ", m.group(2).strip())
                    item["city"] = m.group(3).strip()

            apply_category(Categories.LEISURE_INDOOR_PLAY, item)

            yield item
