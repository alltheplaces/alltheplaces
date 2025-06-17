import re
from typing import Any

import chompjs
from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.react_server_components import parse_rsc
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class McgrathAUSpider(Spider):
    name = "mcgrath_au"
    item_attributes = {
        "brand_wikidata": "Q105290661",
        "brand": "McGrath",
    }
    start_urls = ["https://www.mcgrath.com.au/api/search/getOfficeSearchSuggestion"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for office in chompjs.parse_js_object(response.text)["data"]:
            slug = re.sub(r"\W+", "-", office["name"].strip()).lower()
            yield Request(
                f"https://www.mcgrath.com.au/offices/{slug}-{office['id']}",
                callback=self.parse_office,
                headers={"RSC": "1"},
            )

    def parse_office(self, response: Response, **kwargs: Any) -> Any:
        data = DictParser.get_nested_key(dict(parse_rsc(response.body)), "profile")
        if not data:
            return

        item = DictParser.parse(data)

        item["branch"] = item.pop("name")
        item["website"] = response.url

        oh = OpeningHours()
        oh.add_ranges_from_string(data["openingHours"])
        item["opening_hours"] = oh

        yield item
