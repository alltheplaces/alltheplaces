import json
import re
from typing import Any, Iterable

import chompjs
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc
from locations.structured_data_spider import StructuredDataSpider


class YazigiBRSpider(StructuredDataSpider):
    name = "yazigi_br"
    item_attributes = {"brand": "Yázigi", "brand_wikidata": "Q10394813"}
    start_urls = ["https://escolas.yazigi.com.br/"]
    wanted_types = ["Place"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for url in re.findall(r'\\"siteUrl\\":\\"(https://escolas\.yazigi\.com\.br/[^\\"]+)\\"', response.text):
            yield Request(url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item.pop("image", None)
        branch = re.sub(r"^\s*y[áa]zigi\b[\s\-–:]*", "", item.get("name") or "", flags=re.IGNORECASE)
        if branch:
            item["branch"] = branch.title()

        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(chunk for _, chunk in [chompjs.parse_js_object(script) for script in scripts]).encode()
        if hours := next(DictParser.iter_matching_keys(dict(parse_rsc(rsc)), "horariosJson"), None):
            schedule = json.loads(hours)
            if any(schedule.values()):
                item["opening_hours"] = OpeningHours()
                for day, slots in schedule.items():
                    if not slots:
                        item["opening_hours"].set_closed(day)
                    for slot in slots:
                        item["opening_hours"].add_range(day, slot["open"], slot["close"])

        apply_category(Categories.LANGUAGE_SCHOOL, item)
        yield item
