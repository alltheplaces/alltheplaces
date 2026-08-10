import re
from typing import Any

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_ES, OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc
from locations.user_agents import BROWSER_DEFAULT


class LiverpoolMXSpider(Spider):
    name = "liverpool_mx"
    item_attributes = {"brand": "Liverpool", "brand_wikidata": "Q1143318"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    start_urls = ["https://www.liverpool.com.mx/tienda/browse/storelocator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join(s for n, s in objs if isinstance(s, str)).encode()
        data = dict(parse_rsc(rsc))

        for store in DictParser.get_nested_key(data, "stores") or []:
            if not store["name"].startswith("Liverpool"):
                continue
            yield from self.parse_store(store)

    def parse_store(self, store: dict) -> Any:
        item = Feature()
        item["ref"] = str(store["storeId"])
        item["branch"] = store["name"].replace("Liverpool ", "")
        item["lat"], item["lon"] = store["location"]["coordinates"]
        item["image"] = store.get("photo")

        address = re.sub(r"(?si)Tel:.+|Tel\.\s*.*", "", store["htmlDescription"])
        address = re.sub(r"(?si)<.*?>|\s{2,}", " ", address).strip()
        item["addr_full"] = address
        item["phone"] = store["address"].get("phoneNumber")

        item["opening_hours"] = OpeningHours()
        for rule in store.get("openingHours") or []:
            item["opening_hours"].add_range(DAYS_ES[rule["day"]], rule["open"], rule["close"])

        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
