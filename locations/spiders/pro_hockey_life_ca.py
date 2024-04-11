import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS, OpeningHours


class ProHockeyLifeCASpider(Spider):
    name = "pro_hockey_life_ca"
    item_attributes = {"brand": "Pro Hockey Life", "brand_wikidata": "Q123466336"}
    start_urls = ["https://www.prohockeylife.com/pages/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield response.follow(url=re.search(r'jsonFile="(.+)\?.+";', response.text).group(1), callback=self.parse_json)

    def parse_json(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location["store_number"]
            item["branch"] = item.pop("name")
            item["website"] = "https://www.prohockeylife.com/pages/pro-hockey-life-{}".format(
                re.sub(r"\s+", "-", location["name"].lower())
            )

            item["opening_hours"] = OpeningHours()
            for day in map(str.lower, DAYS_3_LETTERS):
                item["opening_hours"].add_range(day, location[f"{day}_opening"], location[f"{day}_closing"])

            yield item
