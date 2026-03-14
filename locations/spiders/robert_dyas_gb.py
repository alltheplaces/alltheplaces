import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RobertDyasGBSpider(Spider):
    name = "robert_dyas_gb"
    item_attributes = {"brand": "Robert Dyas", "brand_wikidata": "Q7343720"}
    start_urls = ["https://www.robertdyas.co.uk/storefinder"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Host": "www.robertdyas.co.uk"}}
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripttext = response.xpath('//script[contains(text(), "Astound_StoreLocator")]').get()
        data = re.search(r'(?<="data" : ).*(?=,\s+"template")', scripttext).group(0)
        pattern = re.compile(r"^(\w\w) (\d\d:\d\d)-(\d\d:\d\d)$")
        for location in json.loads(data)["locations"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            item["email"] = location["cs_email"]

            item["opening_hours"] = OpeningHours()
            for rule in location["hours"].split(", "):
                if m := pattern.match(rule):
                    item["opening_hours"].add_range(*m.groups())

            apply_category(Categories.SHOP_HARDWARE, item)

            yield item
