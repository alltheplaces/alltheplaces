from typing import Iterable

import chompjs
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc
from locations.user_agents import BROWSER_DEFAULT


class McgrathAUSpider(Spider):
    name = "mcgrath_au"
    item_attributes = {"brand": "McGrath", "brand_wikidata": "Q105290661"}
    start_urls = ["https://www.mcgrath.com.au/api/search/getOfficeSearchSuggestion?query=%20"]
    requires_proxy = True
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}

    def parse(self, response: Response) -> Iterable[Request]:
        for office in chompjs.parse_js_object(response.text)["data"]:
            yield response.follow(office["url"], callback=self.parse_office)

    def parse_office(self, response: Response) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = DictParser.get_nested_key(dict(parse_rsc(rsc)), "profile")
        if not data:
            return

        data.update(data.pop("address")[0])
        data.pop("region")
        item = DictParser.parse(data)

        item["ref"] = data["salesforceId"]
        item["branch"] = item.pop("name")
        item["phone"] = data["firstPhoneNumber"]
        item["website"] = response.url

        oh = OpeningHours()
        oh.add_ranges_from_string(
            " ".join(
                child["text"]
                for paragraph in data["openingHours"]["root"]["children"]
                for child in paragraph["children"]
            )
        )
        item["opening_hours"] = oh

        apply_category(Categories.OFFICE_ESTATE_AGENT, item)

        yield item
