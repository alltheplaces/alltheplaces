import re

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.react_server_components import parse_rsc


class McgrathAUSpider(Spider):
    name = "mcgrath_au"
    item_attributes = {
        "brand_wikidata": "Q105290661",
        "brand": "McGrath",
    }
    start_urls = ["https://www.mcgrath.com.au/api/search/getOfficeSearchSuggestion"]

    def parse(self, response):
        for office in response.json()["data"]:
            slug = re.sub(r"\W+", "-", office["name"].strip()).lower()
            yield Request(
                f"https://www.mcgrath.com.au/offices/{slug}-{office['id']}",
                callback=self.parse_office,
                headers={"RSC": "1"},
            )

    def parse_office(self, response):
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
